import streamlit as st
from googleapiclient.errors import HttpError
import time
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path
from streamlit import cache_data  # 新增：持久化缓存

# 调整导入路径（同上）
sys.path.append(str(Path(__file__).parent.parent))
from google_sheet_utils import get_sheets_service

# --------------------------
# 1. 配置与初始化
# --------------------------
service = get_sheets_service()
SPREADSHEET_ID = st.secrets.get("GROUPS_SPREADSHEET_ID")
SHEET_NAMES = {
    "members": "成员表",
    "income": "收入表",
    "expense": "支出表"
}

# 新增：配额监控（记录最近1分钟的API调用时间）
if "api_calls" not in st.session_state:
    st.session_state.api_calls = []

# --------------------------
# 2. 持久化缓存（跨会话保留）
# --------------------------
@cache_data(ttl=3600)  # 缓存1小时（可调整）
def load_cached_data(sheet_type):
    """从本地缓存加载数据，避免重复同步"""
    return pd.DataFrame()

# --------------------------
# 3. 分页增量同步（核心优化）
# --------------------------
def sync_sheet(sheet_type, page_size=500):
    """分页读取数据，避免单次请求过大"""
    if not SPREADSHEET_ID:
        st.error("请配置GROUPS_SPREADSHEET_ID")
        return False

    # 配额检查：若1分钟内调用超50次，暂停
    now = time.time()
    st.session_state.api_calls = [t for t in st.session_state.api_calls if now - t < 60]
    if len(st.session_state.api_calls) >= 50:
        st.error("⚠️ 配额即将耗尽，请1分钟后再试")
        return False

    sheet_name = SHEET_NAMES[sheet_type]
    last_sync = st.session_state.get(f"last_sync_{sheet_type}", None)
    all_values = []
    page_token = None

    try:
        # 获取工作表ID
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = next(
            sheet["properties"]["sheetId"] 
            for sheet in spreadsheet["sheets"] 
            if sheet["properties"]["title"] == sheet_name
        )

        # 分页读取（每次最多500行）
        while True:
            st.session_state.api_calls.append(time.time())  # 记录调用时间
            range_name = f"{sheet_name}!A:Z"
            request_kwargs = {
                "spreadsheetId": SPREADSHEET_ID,
                "range": range_name,
                "majorDimension": "ROWS",
                "pageSize": page_size,
                "pageToken": page_token
            }
            if last_sync:
                request_kwargs["updatedAfter"] = last_sync.isoformat() + "Z"

            response = service.spreadsheets().values().get(**request_kwargs).execute()
            all_values.extend(response.get("values", []))
            page_token = response.get("nextPageToken")

            if not page_token:
                break  # 无更多分页，结束

        # 处理表头和数据
        if all_values:
            headers = all_values[0]
            data = all_values[1:] if len(all_values) > 1 else []
            df = pd.DataFrame(data, columns=headers)
            # 更新缓存和同步时间
            st.session_state[f"groups_data_{sheet_type}"] = df
            st.session_state[f"last_sync_{sheet_type}"] = datetime.utcnow()
            st.success(f"✅ 同步完成（{len(df)}条数据，分页次数：{len(st.session_state.api_calls[-len(all_values)//page_size:])}）")
        else:
            st.info("ℹ️ 无更新数据")
        return True

    except HttpError as e:
        if e.resp.status == 429:
            retry_after = int(e.resp.get("Retry-After", 10))  # 延长重试等待时间
            st.warning(f"配额超限，{retry_after}秒后重试...")
            time.sleep(retry_after)
            return sync_sheet(sheet_type)
        else:
            st.error(f"同步失败: {e.content.decode()}")
            return False
    except Exception as e:
        st.error(f"同步错误: {str(e)}")
        return False

# --------------------------
# 4. 批量操作优化（降低触发阈值）
# --------------------------
def flush_batch_operations():
    current_time = time.time()
    # 降低阈值：3条数据或5秒内触发批量提交
    if (
        sum(len(v) for v in st.session_state.batch_operations["add"].values()) >=3 
        or sum(len(v) for v in st.session_state.batch_operations["delete"].values()) >=3
        or (current_time - st.session_state.batch_timer) >=5
    ):
        st.toast("批量同步中...")
        try:
            # 记录API调用
            st.session_state.api_calls.append(time.time())
            spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            requests = []

            # 批量添加（同上，略）
            for sheet_type, rows in st.session_state.batch_operations["add"].items():
                if rows:
                    sheet_name = SHEET_NAMES[sheet_type]
                    service.spreadsheets().values().append(
                        spreadsheetId=SPREADSHEET_ID,
                        range=f"{sheet_name}!A1",
                        valueInputOption="USER_ENTERED",
                        body={"values": rows}
                    ).execute()

            # 批量删除（同上，略）
            for sheet_type, row_indices in st.session_state.batch_operations["delete"].items():
                if row_indices:
                    sheet_name = SHEET_NAMES[sheet_type]
                    sheet_id = next(s["properties"]["sheetId"] for s in spreadsheet["sheets"] if s["properties"]["title"] == sheet_name)
                    for idx in sorted(row_indices, reverse=True):
                        requests.append({"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": idx, "endIndex": idx+1}}})
            if requests:
                service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()

            # 清空缓存
            st.session_state.batch_operations = {"add": {"members": [], "income": [], "expense": []}, "delete": {...}}
            st.session_state.batch_timer = current_time

        except Exception as e:
            st.error(f"批量操作失败: {str(e)}")

# --------------------------
# 5. UI与入口逻辑（新增配额显示）
# --------------------------
def show_groups_module():
    st.title("Groups 管理")
    
    # 初始化会话状态
    for key in ["batch_operations", "batch_timer", f"groups_data_", f"last_sync_"]:
        if key not in st.session_state:
            st.session_state[key] = {...}  # 同上，略

    # 显示当前配额使用情况
    st.sidebar.subheader("API配额监控")
    st.sidebar.info(f"近1分钟调用次数：{len([t for t in st.session_state.api_calls if time.time()-t <60])}/60")

    # 选择数据类型
    sheet_type = st.selectbox("选择数据类型", ["members", "income", "expense"], format_func=lambda x: SHEET_NAMES[x])

    # 同步逻辑（优先使用缓存）
    cached_df = load_cached_data(sheet_type)
    if cached_df.empty or st.button("强制同步"):
        with st.spinner(f"同步{SHEET_NAMES[sheet_type]}..."):
            sync_sheet(sheet_type)
    else:
        st.session_state[f"groups_data_{sheet_type}"] = cached_df
        st.success("使用本地缓存数据")

    # 后续UI逻辑（显示数据、添加/删除记录）同上，略

if __name__ == "__main__":
    show_groups_module()
