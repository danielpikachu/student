# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
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
    return sheet_handler.get_worksheet(spreadsheet_name=spreadsheet_name, worksheet_name=worksheet_name)

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
        st.session_state[cache_key] = {"worksheet": worksheet, "time": datetime.now()}
        return worksheet
    except Exception as e:
        st.error(f"获取{group_name}工作表失败: {str(e)}")
        return None

def load_group_data(worksheet):
    """从工作表加载小组数据"""
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
            
            if current_section == "members" and row[0].strip() and row[1].strip():
                data["members"].append({
                    "Name": row[0],
                    "StudentID": row[1],
                    "Position": row[2] if len(row) > 2 else "",
                    "Contact": row[3] if len(row) > 3 else ""
                })
            elif current_section == "earnings" and row[0].strip() and row[1].strip():
                try:
                    date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = row[0]
                data["earnings"].append({
                    "Date": formatted_date,
                    "Amount": float(row[1]) if row[1] else 0.0,
                    "Description": row[2]
                })
            elif current_section == "reimbursements" and row[0].strip() and row[1].strip():
                try:
                    date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = row[0]
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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((HttpError, ConnectionError))
)
def update_worksheet_section(worksheet, section_title, new_data):
    """安全更新工作表区域的方法"""
    all_values = worksheet.get_all_values()
    total_rows = len(all_values)
    section_row = None
    
    # 查找区域标题行（1-based）
    for i, row in enumerate(all_values, 1):
        if row[0].strip() == section_title:
            section_row = i
            break
    
    if not section_row:
        st.error(f"未找到区域: {section_title}")
        return False
    
    data_start_1based = section_row + 2  # 标题行+2是数据起始行
    
    # 计算数据结束行
    data_end_1based = None
    for i in range(data_start_1based - 1, total_rows):
        if all_values[i][0].strip() in ["Members", "Earnings", "Reimbursements"]:
            data_end_1based = i
            break
    if data_end_1based is None:
        data_end_1based = total_rows
    
    # 确保删除范围有效
    if data_start_1based <= data_end_1based and data_start_1based <= total_rows:
        rows_to_delete = data_end_1based - data_start_1based + 1
        if rows_to_delete > 0:
            worksheet.delete_rows(data_start_1based, rows_to_delete)
    
    # 插入新数据
    if new_data:
        for i, row in enumerate(new_data):
            worksheet.insert_row(row, data_start_1based + i)
    
    return True

def save_members(worksheet, members):
    if not worksheet or not members:
        return False
    try:
        rows = [[m["Name"], m["StudentID"], m["Position"], m["Contact"]] for m in members]
        return update_worksheet_section(worksheet, "Members", rows)
    except Exception as e:
        st.error(f"保存成员失败: {str(e)}")
        return False

def save_earnings(worksheet, earnings):
    if not worksheet or not earnings:
        return False
    try:
        rows = [[e["Date"], e["Amount"], e["Description"], ""] for e in earnings]
        return update_worksheet_section(worksheet, "Earnings", rows)
    except Exception as e:
        st.error(f"保存收入失败: {str(e)}")
        return False

def save_reimbursements(worksheet, reimbursements):
    if not worksheet or not reimbursements:
        return False
    try:
        rows = [[r["Date"], r["Amount"], r["Description"], r["Status"]] for r in reimbursements]
        return update_worksheet_section(worksheet, "Reimbursements", rows)
    except Exception as e:
        st.error(f"保存报销失败: {str(e)}")
        return False

def render_groups():
    add_custom_css()
    st.header("👥 小组管理 (Groups Management)")
    st.write("管理小组成员、收入和报销请求")
    st.divider()

    sheet_handler = init_google_sheet_handler()
    group_names = [f"Group{i}" for i in range(1, 9)]
    tabs = st.tabs(group_names)
    
    for i, tab in enumerate(tabs):
        group_name = group_names[i]
        with tab:
            # 初始化会话状态
            state_key = f"grp_{group_name}_data"
            if state_key not in st.session_state:
                st.session_state[state_key] = {"members": [], "earnings": [], "reimbursements": []}
            
            loaded_key = f"grp_{group_name}_loaded"
            if loaded_key not in st.session_state:
                st.session_state[loaded_key] = False
            
            # 获取工作表
            worksheet = get_group_worksheet(sheet_handler, group_name)
            
            # 首次加载数据
            if not st.session_state[loaded_key] and worksheet:
                with st.spinner(f"加载{group_name}数据..."):
                    data = load_group_data(worksheet)
                    st.session_state[state_key] = data
                    st.session_state[loaded_key] = True
                    st.success(f"{group_name}数据加载完成")
            
            group_data = st.session_state[state_key]
            
            # 1. 小组成员管理（核心修改）
            st.subheader("👥 小组成员")
            with st.container(border=True):
                # 显示成员表格
                if group_data["members"]:
                    st.dataframe(
                        pd.DataFrame(group_data["members"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("暂无成员")
                
                # 添加成员表单（使用容器确保组件渲染顺序）
                with st.expander("➕ 添加新成员"):
                    # 使用容器确保所有输入框先渲染
                    input_container = st.container()
                    button_container = st.container()
                    
                    # 定义输入框key
                    name_key = f"name_{group_name}"
                    id_key = f"id_{group_name}"
                    pos_key = f"pos_{group_name}"
                    contact_key = f"contact_{group_name}"
                    
                    # 先渲染所有输入框（关键！确保组件已创建）
                    with input_container:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.text_input("姓名 *", key=name_key, placeholder="必填")
                            st.text_input("学号 *", key=id_key, placeholder="必填")
                        with col2:
                            st.text_input("职位", key=pos_key, placeholder="可选")
                            st.text_input("联系方式", key=contact_key, placeholder="可选")
                    
                    # 再渲染按钮
                    with button_container:
                        if st.button("确认添加", key=f"add_{group_name}"):
                            # 获取输入值
                            new_name = st.session_state.get(name_key, "").strip()
                            new_student_id = st.session_state.get(id_key, "").strip()
                            new_position = st.session_state.get(pos_key, "").strip()
                            new_contact = st.session_state.get(contact_key, "").strip()
                            
                            # 验证必填项
                            if not new_name:
                                st.error("请填写姓名（必填项）")
                            elif not new_student_id:
                                st.error("请填写学号（必填项）")
                            else:
                                # 检查重复
                                if any(m["StudentID"] == new_student_id for m in group_data["members"]):
                                    st.error("该学号已存在")
                                else:
                                    # 更新本地状态
                                    new_member = {
                                        "Name": new_name,
                                        "StudentID": new_student_id,
                                        "Position": new_position,
                                        "Contact": new_contact
                                    }
                                    group_data["members"].append(new_member)
                                    st.session_state[state_key] = group_data
                                    
                                    # 同步到Google Sheet
                                    with st.spinner("同步中..."):
                                        if worksheet and save_members(worksheet, group_data["members"]):
                                            st.success("添加成功并同步！")
                                            # 关键修复：使用get方法安全访问，不直接修改可能未渲染的组件
                                            if name_key in st.session_state:
                                                st.session_state[name_key] = ""
                                            if id_key in st.session_state:
                                                st.session_state[id_key] = ""
                                            if pos_key in st.session_state:
                                                st.session_state[pos_key] = ""
                                            if contact_key in st.session_state:
                                                st.session_state[contact_key] = ""
                                        else:
                                            st.warning("本地添加成功，同步失败")
            
            # 2. 小组收入管理（采用相同安全模式）
            st.subheader("💰 小组收入")
            with st.container(border=True):
                if group_data["earnings"]:
                    earnings_df = pd.DataFrame(group_data["earnings"])
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
                    st.markdown(f"**总收入: ¥{earnings_df['Amount'].sum():.2f}**")
                else:
                    st.info("暂无收入记录")
                
                with st.expander("➕ 添加新收入"):
                    earn_inputs = st.container()
                    earn_button = st.container()
                    
                    earn_date_key = f"e_date_{group_name}"
                    earn_amt_key = f"e_amt_{group_name}"
                    earn_desc_key = f"e_desc_{group_name}"
                    
                    with earn_inputs:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            earn_date = st.date_input("日期", datetime.today(), key=earn_date_key)
                        with col2:
                            earn_amount = st.number_input("金额", min_value=0.01, step=0.01, key=earn_amt_key)
                        with col3:
                            st.text_input("描述", key=earn_desc_key)
                    
                    with earn_button:
                        if st.button("确认添加", key=f"add_earn_{group_name}"):
                            earn_desc = st.session_state.get(earn_desc_key, "").strip()
                            if not earn_desc:
                                st.error("请填写收入描述")
                            else:
                                new_earning = {
                                    "Date": earn_date.strftime("%Y-%m-%d"),
                                    "Amount": earn_amount,
                                    "Description": earn_desc
                                }
                                group_data["earnings"].append(new_earning)
                                st.session_state[state_key] = group_data
                                
                                with st.spinner("同步中..."):
                                    if worksheet and save_earnings(worksheet, group_data["earnings"]):
                                        st.success("添加成功并同步！")
                                        if earn_desc_key in st.session_state:
                                            st.session_state[earn_desc_key] = ""
                                    else:
                                        st.warning("本地添加成功，同步失败")
            
            # 3. 报销请求管理（同上）
            st.subheader("📋 报销请求")
            with st.container(border=True):
                if group_data["reimbursements"]:
                    st.dataframe(
                        pd.DataFrame(group_data["reimbursements"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    st.markdown(f"**总报销金额: ¥{sum(r['Amount'] for r in group_data['reimbursements']):.2f}**")
                else:
                    st.info("暂无报销请求")
                
                with st.expander("➕ 提交新报销请求"):
                    req_inputs = st.container()
                    req_button = st.container()
                    
                    req_date_key = f"r_date_{group_name}"
                    req_amt_key = f"r_amt_{group_name}"
                    req_desc_key = f"r_desc_{group_name}"
                    
                    with req_inputs:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            req_date = st.date_input("日期", datetime.today(), key=req_date_key)
                        with col2:
                            req_amount = st.number_input("金额", min_value=0.01, step=0.01, key=req_amt_key)
                        with col3:
                            st.text_input("描述", key=req_desc_key)
                    
                    with req_button:
                        if st.button("提交请求", key=f"add_req_{group_name}"):
                            req_desc = st.session_state.get(req_desc_key, "").strip()
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
                                st.session_state[state_key] = group_data
                                
                                with st.spinner("同步中..."):
                                    if worksheet and save_reimbursements(worksheet, group_data["reimbursements"]):
                                        st.success("添加成功并同步！")
                                        if req_desc_key in st.session_state:
                                            st.session_state[req_desc_key] = ""
                                    else:
                                        st.warning("本地添加成功，同步失败")

if __name__ == "__main__":
    render_groups()
