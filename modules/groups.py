# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from googleapiclient.errors import HttpError

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def add_custom_css():
    """添加自定义CSS样式"""
    st.markdown("""
    <style>
    .section-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .stExpander {
        margin-bottom: 10px;
    }
    .api-hint {
        font-size: 0.85rem;
        color: #666;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def init_google_sheet_handler():
    """初始化Google Sheet处理器"""
    if "sheet_handler" in st.session_state:
        return st.session_state["sheet_handler"]
    
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        handler = GoogleSheetHandler(credentials_path=creds_path)
        st.session_state["sheet_handler"] = handler
        return handler
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((HttpError, ConnectionError))
)
def get_worksheet_with_retry(sheet_handler, spreadsheet_name, worksheet_name):
    """带重试机制的工作表获取方法"""
    return sheet_handler.get_worksheet(
        spreadsheet_name=spreadsheet_name,
        worksheet_name=worksheet_name
    )

def get_group_worksheet(sheet_handler, group_name):
    """获取指定小组的子工作表（带缓存机制）"""
    cache_key = f"worksheet_{group_name}"
    
    if cache_key in st.session_state:
        cache_entry = st.session_state[cache_key]
        if datetime.now() - cache_entry["time"] < timedelta(minutes=5):
            return cache_entry["worksheet"]
    
    if not sheet_handler:
        return None
    
    try:
        worksheet = get_worksheet_with_retry(
            sheet_handler,
            spreadsheet_name="Student",
            worksheet_name=group_name
        )
        st.session_state[cache_key] = {
            "worksheet": worksheet,
            "time": datetime.now()
        }
        return worksheet
    except Exception as e:
        st.error(f"获取{group_name}工作表失败，请确认该工作表已存在: {str(e)}")
        return None

def load_group_data(worksheet):
    """从工作表加载小组数据（成员、收入、报销）"""
    if not worksheet:
        return {"members": [], "earnings": [], "reimbursements": []}
    
    try:
        all_data = worksheet.get_all_values()
        data = {"members": [], "earnings": [], "reimbursements": []}
        current_section = None
        
        for row in all_data:
            if all(cell.strip() == "" for cell in row):
                continue
                
            stripped_first = row[0].strip()
            if stripped_first == "Members":
                current_section = "members"
                continue
            elif stripped_first == "Earnings":
                current_section = "earnings"
                continue
            elif stripped_first == "Reimbursements":
                current_section = "reimbursements"
                continue
            
            if stripped_first in ["Name", "Date"]:
                continue
            
            if current_section == "members":
                if row[0].strip() and row[1].strip():
                    data["members"].append({
                        "Name": row[0],
                        "StudentID": row[1],
                        "Position": row[2],
                        "Contact": row[3]
                    })
            elif current_section == "earnings":
                if row[0].strip() and row[1].strip():
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = row[0]
                        st.warning(f"收入日期格式不正确: {row[0]}, 建议使用YYYY-MM-DD")
                    
                    data["earnings"].append({
                        "Date": formatted_date,
                        "Amount": float(row[1]) if row[1] else 0.0,
                        "Description": row[2]
                    })
            elif current_section == "reimbursements":
                if row[0].strip() and row[1].strip():
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = row[0]
                        st.warning(f"报销日期格式不正确: {row[0]}, 建议使用YYYY-MM-DD")
                    
                    data["reimbursements"].append({
                        "Date": formatted_date,
                        "Amount": float(row[1]) if row[1] else 0.0,
                        "Description": row[2],
                        "Status": row[3] or "Pending"
                    })
        
        return data
    except Exception as e:
        st.error(f"加载小组数据失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}

# 【核心修复点】重写区域更新逻辑，解决endIndex错误
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((HttpError, ConnectionError))
)
def update_worksheet_section(worksheet, section_title, new_data):
    """
    安全更新工作表区域的方法
    1. 定位区域标题行
    2. 从数据起始行删除到表格末尾（避免索引错误）
    3. 插入新数据
    """
    all_values = worksheet.get_all_values()
    section_row = None  # 区域标题所在行（1-based索引）
    
    # 查找区域标题行
    for i, row in enumerate(all_values, 1):
        if row[0].strip() == section_title:
            section_row = i
            break
    
    if not section_row:
        st.error(f"未找到区域: {section_title}")
        return False
    
    # 数据区域起始行 = 标题行 + 2（标题行+1是表头）
    data_start_row = section_row + 2
    total_rows = len(all_values)
    
    # 清除现有数据（如果数据起始行在表格范围内）
    if data_start_row <= total_rows:
        # 计算要删除的行数（从数据起始行到最后一行）
        rows_to_delete = total_rows - data_start_row + 1
        if rows_to_delete > 0:
            worksheet.delete_rows(data_start_row, rows_to_delete)
    
    # 插入新数据
    if new_data:
        for i, row in enumerate(new_data):
            worksheet.insert_row(row, data_start_row + i)
    
    return True

# 【仅修改调用方式】保持原有函数接口，内部使用新的更新方法
def save_members(worksheet, members):
    if not worksheet or not members:
        return False
        
    try:
        rows_to_insert = [
            [m["Name"], m["StudentID"], m["Position"], m["Contact"]]
            for m in members
        ]
        return update_worksheet_section(worksheet, "Members", rows_to_insert)
    except Exception as e:
        st.error(f"保存成员数据到Google Sheet失败: {str(e)}")
        return False

def save_earnings(worksheet, earnings):
    if not worksheet or not earnings:
        return False
        
    try:
        rows_to_insert = [
            [e["Date"], e["Amount"], e["Description"], ""]
            for e in earnings
        ]
        return update_worksheet_section(worksheet, "Earnings", rows_to_insert)
    except Exception as e:
        st.error(f"保存收入数据到Google Sheet失败: {str(e)}")
        return False

def save_reimbursements(worksheet, reimbursements):
    if not worksheet or not reimbursements:
        return False
        
    try:
        rows_to_insert = [
            [r["Date"], r["Amount"], r["Description"], r["Status"]]
            for r in reimbursements
        ]
        return update_worksheet_section(worksheet, "Reimbursements", rows_to_insert)
    except Exception as e:
        st.error(f"保存报销数据到Google Sheet失败: {str(e)}")
        return False

# 【以下代码完全未变动】保持原有界面和业务逻辑
def render_groups():
    add_custom_css()
    st.header("👥 小组管理 (Groups Management)")
    st.write("管理小组成员、收入和报销请求")
    st.caption("提示：Google Sheets API有请求频率限制，请勿频繁操作")
    st.divider()

    sheet_handler = init_google_sheet_handler()
    
    group_names = [f"Group{i}" for i in range(1, 9)]
    tabs = st.tabs(group_names)
    
    for i, tab in enumerate(tabs):
        group_name = group_names[i]
        with tab:
            if f"grp_{group_name}_data" not in st.session_state:
                st.session_state[f"grp_{group_name}_data"] = {
                    "members": [], "earnings": [], "reimbursements": []
                }
            
            if f"grp_{group_name}_last_loaded" not in st.session_state:
                st.session_state[f"grp_{group_name}_last_loaded"] = datetime.min
            
            worksheet = get_group_worksheet(sheet_handler, group_name)
            
            now = datetime.now()
            if (now - st.session_state[f"grp_{group_name}_last_loaded"] > timedelta(minutes=5) or 
                f"grp_{group_name}_loaded" not in st.session_state):
                with st.spinner(f"正在自动加载{group_name}的数据..."):
                    data = load_group_data(worksheet)
                    st.session_state[f"grp_{group_name}_data"] = data
                    st.session_state[f"grp_{group_name}_loaded"] = True
                    st.session_state[f"grp_{group_name}_last_loaded"] = now
                    st.success(f"{group_name}数据加载成功！")
            
            col_refresh, col_empty = st.columns([1, 5])
            with col_refresh:
                if st.button("🔄 刷新数据", key=f"grp_{group_name}_load_btn"):
                    last_refresh = st.session_state.get(f"grp_{group_name}_last_refresh", datetime.min)
                    if now - last_refresh < timedelta(seconds=10):
                        st.warning("请不要频繁刷新，至少间隔10秒")
                    else:
                        with st.spinner("正在从Google Sheets刷新数据..."):
                            data = load_group_data(worksheet)
                            st.session_state[f"grp_{group_name}_data"] = data
                            st.session_state[f"grp_{group_name}_last_loaded"] = now
                            st.session_state[f"grp_{group_name}_last_refresh"] = now
                            st.success("数据刷新成功！")
            
            group_data = st.session_state[f"grp_{group_name}_data"]
            
            # 小组成员管理
            st.subheader("👥 小组成员 (Group Members)")
            with st.container(border=True):
                if group_data["members"]:
                    st.dataframe(
                        pd.DataFrame(group_data["members"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("当前小组暂无成员，请添加成员")
                
                with st.expander("➕ 添加新成员", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("姓名", key=f"grp_{group_name}_member_name")
                        new_student_id = st.text_input("学号", key=f"grp_{group_name}_member_id")
                    with col2:
                        new_position = st.text_input("职位", key=f"grp_{group_name}_member_pos")
                        new_contact = st.text_input("联系方式", key=f"grp_{group_name}_member_contact")
                    
                    if st.button("确认添加", key=f"grp_{group_name}_add_member"):
                        if not all([new_name, new_student_id, new_position]):
                            st.error("请填写姓名、学号和职位（必填项）")
                        else:
                            duplicate = any(m["StudentID"] == new_student_id for m in group_data["members"])
                            if duplicate:
                                st.error("该学号已存在于成员列表中")
                            else:
                                group_data["members"].append({
                                    "Name": new_name, "StudentID": new_student_id,
                                    "Position": new_position, "Contact": new_contact
                                })
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("成员已添加到界面，正在同步到Google Sheet...")
                                
                                with st.spinner("正在同步到Google Sheet..."):
                                    if save_members(worksheet, group_data["members"]):
                                        st.success("成员已成功同步到Google Sheet！")
            
            # 小组收入管理
            st.subheader("💰 小组收入 (Group Earnings)")
            with st.container(border=True):
                if group_data["earnings"]:
                    earnings_df = pd.DataFrame(group_data["earnings"])
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
                    total_earning = earnings_df["Amount"].sum()
                    st.markdown(f"**总收入: ¥{total_earning:.2f}**")
                else:
                    st.info("当前小组暂无收入记录")
                
                with st.expander("➕ 添加新收入", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        earn_date = st.date_input("日期", datetime.today(), key=f"grp_{group_name}_earn_date")
                    with col2:
                        earn_amount = st.number_input("金额", min_value=0.01, step=0.01, key=f"grp_{group_name}_earn_amt")
                    with col3:
                        earn_desc = st.text_input("描述", key=f"grp_{group_name}_earn_desc")
                    
                    if st.button("确认添加", key=f"grp_{group_name}_add_earning"):
                        if not earn_desc:
                            st.error("请填写收入描述")
                        else:
                            new_earning = {
                                "Date": earn_date.strftime("%Y-%m-%d"),
                                "Amount": earn_amount,
                                "Description": earn_desc
                            }
                            group_data["earnings"].append(new_earning)
                            st.session_state[f"grp_{group_name}_data"] = group_data
                            st.success("收入已添加到界面，正在同步到Google Sheet...")
                            
                            with st.spinner("正在同步到Google Sheet..."):
                                if save_earnings(worksheet, group_data["earnings"]):
                                    st.success("收入已成功同步到Google Sheet！")
                
                if group_data["earnings"]:
                    earn_to_delete = st.selectbox(
                        "选择要删除的收入",
                        [f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" for e in group_data["earnings"]],
                        key=f"grp_{group_name}_del_earn",
                        index=None,
                        placeholder="选择收入项..."
                    )
                    
                    if st.button("删除选中收入", key=f"grp_{group_name}_del_earn_btn"):
                        if earn_to_delete:
                            original_count = len(group_data["earnings"])
                            group_data["earnings"] = [
                                e for e in group_data["earnings"]
                                if f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" != earn_to_delete
                            ]
                            
                            if len(group_data["earnings"]) < original_count:
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("收入已从界面移除，正在同步到Google Sheet...")
                                
                                with st.spinner("正在同步到Google Sheet..."):
                                    if save_earnings(worksheet, group_data["earnings"]):
                                        st.success("收入已成功从Google Sheet删除！")
            
            # 报销请求管理
            st.subheader("📋 报销请求 (Reimbursement Requests)")
            with st.container(border=True):
                if group_data["reimbursements"]:
                    st.dataframe(
                        pd.DataFrame(group_data["reimbursements"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    total_reimburse = sum(r["Amount"] for r in group_data["reimbursements"])
                    st.markdown(f"**总报销金额: ¥{total_reimburse:.2f}**")
                else:
                    st.info("当前小组暂无报销请求")
                
                with st.expander("➕ 提交新报销请求", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        req_date = st.date_input("日期", datetime.today(), key=f"grp_{group_name}_req_date")
                    with col2:
                        req_amount = st.number_input("金额", min_value=0.01, step=0.01, key=f"grp_{group_name}_req_amt")
                    with col3:
                        req_desc = st.text_input("描述", key=f"grp_{group_name}_req_desc")
                    
                    if st.button("提交请求", key=f"grp_{group_name}_add_req"):
                        if not req_desc:
                            st.error("请填写报销描述")
                        else:
                            new_reimbursement = {
                                "Date": req_date.strftime("%Y-%m-%d"),
                                "Amount": req_amount,
                                "Description": req_desc,
                                "Status": "Pending"
                            }
                            group_data["reimbursements"].append(new_reimbursement)
                            st.session_state[f"grp_{group_name}_data"] = group_data
                            st.success("报销请求已添加到界面，正在同步到Google Sheet...")
                            
                            with st.spinner("正在同步到Google Sheet..."):
                                if save_reimbursements(worksheet, group_data["reimbursements"]):
                                    st.success("报销请求已成功同步到Google Sheet！")
                
                if group_data["reimbursements"]:
                    req_to_update = st.selectbox(
                        "选择要更新的报销请求",
                        [f"{r['Date']} - ¥{r['Amount']} - {r['Description']} ({r['Status']})" for r in group_data["reimbursements"]],
                        key=f"grp_{group_name}_upd_req",
                        index=None,
                        placeholder="选择报销项..."
                    )
                    
                    new_status = st.selectbox(
                        "更新状态为",
                        ["Pending", "Approved", "Rejected"],
                        key=f"grp_{group_name}_req_status"
                    )
                    
                    if st.button("更新状态", key=f"grp_{group_name}_upd_req_btn"):
                        if req_to_update:
                            updated = False
                            for req in group_data["reimbursements"]:
                                req_str = f"{req['Date']} - ¥{req['Amount']} - {req['Description']} ({req['Status']})"
                                if req_str == req_to_update and req["Status"] != new_status:
                                    req["Status"] = new_status
                                    updated = True
                                    break
                            
                            if updated:
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("报销状态已在界面更新，正在同步到Google Sheet...")
                                
                                with st.spinner("正在同步到Google Sheet..."):
                                    if save_reimbursements(worksheet, group_data["reimbursements"]):
                                        st.success("报销状态已成功同步到Google Sheet！")

if __name__ == "__main__":
    render_groups()
