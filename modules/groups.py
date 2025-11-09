import streamlit as st
from googleapiclient.errors import HttpError
import time
from datetime import datetime
import pandas as pd
# 关键调整：从上级目录导入google_sheet_utils（因groups.py在modules文件夹内）
import sys
from pathlib import Path
# 将项目根目录添加到Python路径（确保能找到google_sheet_utils）
sys.path.append(str(Path(__file__).parent.parent))
from google_sheet_utils import get_sheets_service, get_gspread_client

# --------------------------
# 1. 初始化配置（依赖工具类）
# --------------------------
service = get_sheets_service()  # 复用工具类的认证服务
gc = get_gspread_client()

SPREADSHEET_ID = st.secrets.get("GROUPS_SPREADSHEET_ID")
SHEET_NAMES = {
    "members": "成员表",
    "income": "收入表",
    "expense": "支出表"
}

# --------------------------
# 2. 本地缓存与状态管理（不变）
# --------------------------
def init_session_state():
    if "groups_data" not in st.session_state:
        st.session_state.groups_data = {
            "members": pd.DataFrame(),
            "income": pd.DataFrame(),
            "expense": pd.DataFrame()
        }
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = {
            "members": None,
            "income": None,
            "expense": None
        }
    if "batch_operations" not in st.session_state:
        st.session_state.batch_operations = {
            "add": {"members": [], "income": [], "expense": []},
            "delete": {"members": [], "income": [], "expense": []}
        }
    if "batch_timer" not in st.session_state:
        st.session_state.batch_timer = time.time()

# --------------------------
# 3. 增量同步逻辑（不变，依赖工具类服务）
# --------------------------
def sync_sheet(sheet_type):
    if not SPREADSHEET_ID:
        st.error("请配置GROUPS_SPREADSHEET_ID")
        return False

    sheet_name = SHEET_NAMES[sheet_type]
    last_sync = st.session_state.last_sync_time[sheet_type]
    
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_id = next(
            sheet["properties"]["sheetId"] 
            for sheet in spreadsheet["sheets"] 
            if sheet["properties"]["title"] == sheet_name
        )

        range_name = f"{sheet_name}!A:Z"
        request_kwargs = {
            "spreadsheetId": SPREADSHEET_ID,
            "range": range_name,
            "majorDimension": "ROWS"
        }
        if last_sync:
            request_kwargs["updatedAfter"] = last_sync.isoformat() + "Z"

        response = service.spreadsheets().values().get(** request_kwargs).execute()
        values = response.get("values", [])

        if values:
            df = pd.DataFrame(values[1:], columns=values[0])
            st.session_state.groups_data[sheet_type] = df
            st.session_state.last_sync_time[sheet_type] = datetime.utcnow()
            st.success(f"✅ {sheet_name}同步完成（{len(df)}条数据）")
        else:
            st.info(f"ℹ️ {sheet_name}无更新数据")
        return True

    except HttpError as e:
        if e.resp.status == 429:
            retry_after = int(e.resp.get("Retry-After", 5))
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
# 4. 批量操作逻辑（不变）
# --------------------------
def flush_batch_operations():
    current_time = time.time()
    if (
        sum(len(v) for v in st.session_state.batch_operations["add"].values()) >=5 
        or sum(len(v) for v in st.session_state.batch_operations["delete"].values()) >=5
        or (current_time - st.session_state.batch_timer) >=10
    ):
        st.toast("正在批量同步数据...")
        try:
            spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            requests = []

            # 批量添加
            for sheet_type, rows in st.session_state.batch_operations["add"].items():
                if not rows:
                    continue
                sheet_name = SHEET_NAMES[sheet_type]
                service.spreadsheets().values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f"{sheet_name}!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": rows}
                ).execute()
                st.success(f"✅ 批量添加{len(rows)}条{sheet_name}数据")

            # 批量删除
            for sheet_type, row_indices in st.session_state.batch_operations["delete"].items():
                if not row_indices:
                    continue
                sheet_name = SHEET_NAMES[sheet_type]
                sheet_id = next(
                    sheet["properties"]["sheetId"] 
                    for sheet in spreadsheet["sheets"] 
                    if sheet["properties"]["title"] == sheet_name
                )
                for row_idx in sorted(row_indices, reverse=True):
                    requests.append({
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_idx,
                                "endIndex": row_idx + 1
                            }
                        }
                    })
                if requests:
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=SPREADSHEET_ID,
                        body={"requests": requests}
                    ).execute()
                    st.success(f"✅ 批量删除{len(row_indices)}条{sheet_name}数据")

            # 清空缓存
            st.session_state.batch_operations = {
                "add": {"members": [], "income": [], "expense": []},
                "delete": {"members": [], "income": [], "expense": []}
            }
            st.session_state.batch_timer = current_time

        except Exception as e:
            st.error(f"批量操作失败: {str(e)}")

# --------------------------
# 5. 操作接口与UI（不变）
# --------------------------
def add_record(sheet_type, data):
    st.session_state.batch_operations["add"][sheet_type].append(data)
    flush_batch_operations()

def delete_record(sheet_type, row_index):
    st.session_state.batch_operations["delete"][sheet_type].append(row_index)
    flush_batch_operations()

def show_groups_module():
    st.title("Groups 管理")
    init_session_state()

    sheet_type = st.selectbox("选择数据类型", ["members", "income", "expense"], 
                             format_func=lambda x: SHEET_NAMES[x])

    if st.button("同步数据") or st.session_state.groups_data[sheet_type].empty:
        with st.spinner(f"正在同步{SHEET_NAMES[sheet_type]}..."):
            sync_sheet(sheet_type)

    st.subheader(f"{SHEET_NAMES[sheet_type]}数据")
    df = st.session_state.groups_data[sheet_type]
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        delete_idx = st.number_input("输入要删除的行索引（从0开始）", min_value=0, max_value=len(df)-1, step=1)
        if st.button("删除选中行"):
            delete_record(sheet_type, delete_idx)
            st.session_state.groups_data[sheet_type] = df.drop(index=delete_idx).reset_index(drop=True)
            st.experimental_rerun()
    else:
        st.info("暂无数据，请先同步")

    st.subheader(f"添加新{sheet_type}记录")
    if sheet_type == "members":
        name = st.text_input("成员姓名")
        role = st.text_input("角色")
        if st.button("添加成员"):
            add_record("members", [name, role, datetime.now().strftime("%Y-%m-%d")])
    elif sheet_type == "income":
        amount = st.number_input("收入金额", min_value=0)
        source = st.text_input("收入来源")
        if st.button("添加收入"):
            add_record("income", [source, amount, datetime.now().strftime("%Y-%m-%d")])
    elif sheet_type == "expense":
        amount = st.number_input("支出金额", min_value=0)
        reason = st.text_input("支出原因")
        if st.button("添加支出"):
            add_record("expense", [reason, amount, datetime.now().strftime("%Y-%m-%d")])

if __name__ == "__main__":
    show_groups_module()
