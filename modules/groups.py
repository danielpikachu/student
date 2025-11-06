# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def add_custom_css():
    st.markdown("""
    <style>
    .section-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

def init_google_sheet_handler():
    """初始化Google Sheet处理器"""
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        return GoogleSheetHandler(credentials_path=creds_path)
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")
        return None

def get_or_create_worksheet(sheet_handler, group_name):
    """获取或创建指定小组的工作表"""
    if not sheet_handler:
        return None
    
    try:
        # 尝试获取现有工作表
        return sheet_handler.get_worksheet(
            spreadsheet_name="GroupsData",
            worksheet_name=group_name
        )
    except:
        # 工作表不存在，创建新的
        try:
            # 确保 spreadsheet 存在
            sheet_handler.create_spreadsheet("GroupsData")
            # 创建新工作表
            worksheet = sheet_handler.create_worksheet(
                spreadsheet_name="GroupsData",
                worksheet_name=group_name
            )
            
            # 初始化表头
            # 成员表
            worksheet.append_row(["Members", "", "", ""])
            worksheet.append_row(["Name", "StudentID", "Position", "Contact"])
            # 收入表
            worksheet.append_row(["", "", "", ""])
            worksheet.append_row(["Earnings", "", "", ""])
            worksheet.append_row(["Date", "Amount", "Description", ""])
            # 报销表
            worksheet.append_row(["", "", "", ""])
            worksheet.append_row(["Reimbursements", "", "", ""])
            worksheet.append_row(["Date", "Amount", "Description", "Status"])
            
            return worksheet
        except Exception as e:
            st.error(f"创建工作表失败: {str(e)}")
            return None

def load_group_data(worksheet):
    """从工作表加载小组数据"""
    if not worksheet:
        return {"members": [], "earnings": [], "reimbursements": []}
    
    try:
        all_data = worksheet.get_all_values()
        data = {"members": [], "earnings": [], "reimbursements": []}
        section = None
        
        for row in all_data:
            if row[0] == "Members":
                section = "members"
                continue
            elif row[0] == "Earnings":
                section = "earnings"
                continue
            elif row[0] == "Reimbursements":
                section = "reimbursements"
                continue
            
            if not section or not row[0]:
                continue
                
            if section == "members" and row[0] != "Name":  # 跳过表头
                data["members"].append({
                    "Name": row[0],
                    "StudentID": row[1],
                    "Position": row[2],
                    "Contact": row[3]
                })
            elif section == "earnings" and row[0] != "Date":  # 跳过表头
                data["earnings"].append({
                    "Date": row[0],
                    "Amount": float(row[1]) if row[1] else 0,
                    "Description": row[2]
                })
            elif section == "reimbursements" and row[0] != "Date":  # 跳过表头
                data["reimbursements"].append({
                    "Date": row[0],
                    "Amount": float(row[1]) if row[1] else 0,
                    "Description": row[2],
                    "Status": row[3] or "Pending"
                })
        
        return data
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}

def save_member(worksheet, members, name, student_id, position, contact):
    """保存成员到工作表"""
    if not worksheet:
        return False
        
    try:
        # 清空现有成员数据
        all_data = worksheet.get_all_values()
        start_row = None
        end_row = None
        
        # 找到成员区域
        for i, row in enumerate(all_data):
            if row[0] == "Members":
                start_row = i + 2  # 跳过标题行和表头
            elif start_row and row[0] in ["Earnings", "Reimbursements"]:
                end_row = i - 1
                break
        
        if start_row:
            if end_row and end_row >= start_row:
                worksheet.delete_rows(start_row + 1, end_row - start_row + 1)  # 工作表行索引从1开始
            
            # 添加所有成员（包括新的）
            for member in members:
                worksheet.insert_row(
                    [member["Name"], member["StudentID"], member["Position"], member["Contact"]],
                    start_row + 1
                )
        
        return True
    except Exception as e:
        st.error(f"保存成员失败: {str(e)}")
        return False

def save_earning(worksheet, earnings):
    """保存收入到工作表"""
    if not worksheet:
        return False
        
    try:
        all_data = worksheet.get_all_values()
        start_row = None
        end_row = None
        
        # 找到收入区域
        for i, row in enumerate(all_data):
            if row[0] == "Earnings":
                start_row = i + 2  # 跳过标题行和表头
            elif start_row and row[0] == "Reimbursements":
                end_row = i - 1
                break
        
        if start_row:
            if end_row and end_row >= start_row:
                worksheet.delete_rows(start_row + 1, end_row - start_row + 1)
            
            # 添加所有收入
            for earning in earnings:
                worksheet.insert_row(
                    [earning["Date"], earning["Amount"], earning["Description"], ""],
                    start_row + 1
                )
        
        return True
    except Exception as e:
        st.error(f"保存收入失败: {str(e)}")
        return False

def save_reimbursement(worksheet, reimbursements):
    """保存报销请求到工作表"""
    if not worksheet:
        return False
        
    try:
        all_data = worksheet.get_all_values()
        start_row = None
        
        # 找到报销区域
        for i, row in enumerate(all_data):
            if row[0] == "Reimbursements":
                start_row = i + 2  # 跳过标题行和表头
                break
        
        if start_row:
            # 清除从start_row到最后的所有行
            max_row = worksheet.row_count
            if max_row > start_row:
                worksheet.delete_rows(start_row + 1, max_row - start_row)
            
            # 添加所有报销请求
            for reimbursement in reimbursements:
                worksheet.insert_row(
                    [reimbursement["Date"], reimbursement["Amount"], 
                     reimbursement["Description"], reimbursement["Status"]],
                    start_row + 1
                )
        
        return True
    except Exception as e:
        st.error(f"保存报销请求失败: {str(e)}")
        return False

def render_groups():
    """渲染群组模块界面（grp_前缀命名空间）"""
    add_custom_css()
    st.header("👥 Groups Management")
    st.write("Manage group members, earnings and reimbursements")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = init_google_sheet_handler()
    
    # 创建8个小组的选项卡
    group_names = [f"Group{i}" for i in range(1, 9)]
    tabs = st.tabs(group_names)
    
    # 为每个小组创建界面
    for i, tab in enumerate(tabs):
        group_name = group_names[i]
        with tab:
            # 初始化会话状态
            if f"grp_{group_name}_data" not in st.session_state:
                st.session_state[f"grp_{group_name}_data"] = {
                    "members": [],
                    "earnings": [],
                    "reimbursements": []
                }
            
            # 获取或创建工作表
            worksheet = get_or_create_worksheet(sheet_handler, group_name)
            
            # 加载数据按钮
            if st.button("🔄 Load Data from Sheet", key=f"grp_{group_name}_load_btn"):
                data = load_group_data(worksheet)
                st.session_state[f"grp_{group_name}_data"] = data
                st.success("Data loaded successfully!")
            
            # 获取当前小组数据
            group_data = st.session_state[f"grp_{group_name}_data"]
            
            # 1. 小组成员名单部分
            st.subheader("👥 Group Members")
            with st.container(border=True):
                # 显示成员表格
                if group_data["members"]:
                    st.dataframe(
                        pd.DataFrame(group_data["members"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No members in this group yet.")
                
                # 添加成员表单
                with st.expander("Add New Member", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Name", key=f"grp_{group_name}_member_name")
                        new_student_id = st.text_input("Student ID", key=f"grp_{group_name}_member_id")
                    with col2:
                        new_position = st.text_input("Position", key=f"grp_{group_name}_member_pos")
                        new_contact = st.text_input("Contact", key=f"grp_{group_name}_member_contact")
                    
                    if st.button("Add Member", key=f"grp_{group_name}_add_member"):
                        if not all([new_name, new_student_id, new_position]):
                            st.error("Please fill in all required fields (Name, Student ID, Position)")
                        else:
                            # 检查重复
                            duplicate = any(
                                m["StudentID"] == new_student_id 
                                for m in group_data["members"]
                            )
                            if duplicate:
                                st.error("A member with this Student ID already exists")
                            else:
                                # 添加到本地数据
                                group_data["members"].append({
                                    "Name": new_name,
                                    "StudentID": new_student_id,
                                    "Position": new_position,
                                    "Contact": new_contact
                                })
                                # 保存到Google Sheet
                                if save_member(worksheet, group_data["members"], new_name, new_student_id, new_position, new_contact):
                                    st.success("Member added successfully!")
                                st.session_state[f"grp_{group_name}_data"] = group_data
            
            # 2. Group Earning部分
            st.subheader("💰 Group Earnings")
            with st.container(border=True):
                # 显示收入表格
                if group_data["earnings"]:
                    earnings_df = pd.DataFrame(group_data["earnings"])
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
                    
                    # 总收入
                    total_earning = earnings_df["Amount"].sum()
                    st.markdown(f"**Total Earnings: ${total_earning:.2f}**")
                else:
                    st.info("No earnings recorded yet.")
                
                # 添加收入表单
                with st.expander("Add New Earning", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        earn_date = st.date_input(
                            "Date", 
                            datetime.today(),
                            key=f"grp_{group_name}_earn_date"
                        )
                    with col2:
                        earn_amount = st.number_input(
                            "Amount ($)", 
                            min_value=0.01, 
                            step=0.01,
                            key=f"grp_{group_name}_earn_amt"
                        )
                    with col3:
                        earn_desc = st.text_input(
                            "Description",
                            key=f"grp_{group_name}_earn_desc"
                        )
                    
                    if st.button("Add Earning", key=f"grp_{group_name}_add_earning"):
                        if not earn_desc:
                            st.error("Please provide a description")
                        else:
                            # 添加到本地数据
                            group_data["earnings"].append({
                                "Date": earn_date.strftime("%Y-%m-%d"),
                                "Amount": earn_amount,
                                "Description": earn_desc
                            })
                            # 保存到Google Sheet
                            if save_earning(worksheet, group_data["earnings"]):
                                st.success("Earning added successfully!")
                            st.session_state[f"grp_{group_name}_data"] = group_data
                
                # 删除收入
                if group_data["earnings"]:
                    earn_to_delete = st.selectbox(
                        "Select earning to delete",
                        [f"{e['Date']} - ${e['Amount']} - {e['Description']}" 
                         for e in group_data["earnings"]],
                        key=f"grp_{group_name}_del_earn",
                        index=None,
                        placeholder="Choose an earning to delete"
                    )
                    
                    if st.button("Delete Selected Earning", key=f"grp_{group_name}_del_earn_btn"):
                        if earn_to_delete:
                            # 找到要删除的收入
                            group_data["earnings"] = [
                                e for e in group_data["earnings"]
                                if f"{e['Date']} - ${e['Amount']} - {e['Description']}" != earn_to_delete
                            ]
                            # 保存到Google Sheet
                            if save_earning(worksheet, group_data["earnings"]):
                                st.success("Earning deleted successfully!")
                            st.session_state[f"grp_{group_name}_data"] = group_data
            
            # 3. Reimbursement Requests部分
            st.subheader("📋 Reimbursement Requests")
            with st.container(border=True):
                # 显示报销请求表格
                if group_data["reimbursements"]:
                    st.dataframe(
                        pd.DataFrame(group_data["reimbursements"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # 总报销金额
                    total_reimburse = sum(r["Amount"] for r in group_data["reimbursements"])
                    st.markdown(f"**Total Reimbursements: ${total_reimburse:.2f}**")
                else:
                    st.info("No reimbursement requests yet.")
                
                # 添加报销请求表单
                with st.expander("Add New Reimbursement Request", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        req_date = st.date_input(
                            "Date", 
                            datetime.today(),
                            key=f"grp_{group_name}_req_date"
                        )
                    with col2:
                        req_amount = st.number_input(
                            "Amount ($)", 
                            min_value=0.01, 
                            step=0.01,
                            key=f"grp_{group_name}_req_amt"
                        )
                    with col3:
                        req_desc = st.text_input(
                            "Description",
                            key=f"grp_{group_name}_req_desc"
                        )
                    
                    if st.button("Submit Request", key=f"grp_{group_name}_add_req"):
                        if not req_desc:
                            st.error("Please provide a description")
                        else:
                            # 添加到本地数据
                            group_data["reimbursements"].append({
                                "Date": req_date.strftime("%Y-%m-%d"),
                                "Amount": req_amount,
                                "Description": req_desc,
                                "Status": "Pending"
                            })
                            # 保存到Google Sheet
                            if save_reimbursement(worksheet, group_data["reimbursements"]):
                                st.success("Reimbursement request submitted!")
                            st.session_state[f"grp_{group_name}_data"] = group_data
                
                # 更新报销状态
                if group_data["reimbursements"]:
                    req_to_update = st.selectbox(
                        "Select request to update status",
                        [f"{r['Date']} - ${r['Amount']} - {r['Description']} ({r['Status']})" 
                         for r in group_data["reimbursements"]],
                        key=f"grp_{group_name}_upd_req",
                        index=None,
                        placeholder="Choose a request to update"
                    )
                    
                    new_status = st.selectbox(
                        "New Status",
                        ["Pending", "Approved", "Rejected"],
                        key=f"grp_{group_name}_req_status"
                    )
                    
                    if st.button("Update Status", key=f"grp_{group_name}_upd_req_btn"):
                        if req_to_update:
                            # 更新状态
                            for req in group_data["reimbursements"]:
                                req_str = f"{req['Date']} - ${req['Amount']} - {req['Description']} ({req['Status']})"
                                if req_str == req_to_update:
                                    req["Status"] = new_status
                                    break
                            # 保存到Google Sheet
                            if save_reimbursement(worksheet, group_data["reimbursements"]):
                                st.success("Status updated successfully!")
                            st.session_state[f"grp_{group_name}_data"] = group_data
