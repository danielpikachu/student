# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def init_google_sheet():
    """初始化Google Sheets连接"""
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        return sheet_handler
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
        return None

def sync_group_data(sheet_handler, group_id):
    """同步指定组的数据到会话状态"""
    # 初始化三个数据表
    for data_type in ["members", "earnings"]:
        state_key = f"grp_{group_id}_{data_type}"
        if state_key not in st.session_state:
            st.session_state[state_key] = []

    if not sheet_handler:
        return

    try:
        # 成员表同步
        members_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name=f"Group{group_id}Members"
        )
        if members_sheet:
            all_data = members_sheet.get_all_values()
            expected_headers = ["uuid", "name", "student_id", "position", "contact"]
            
            if not all_data or all_data[0] != expected_headers:
                members_sheet.clear()
                members_sheet.append_row(expected_headers)
                members = []
            else:
                members = [
                    {
                        "uuid": row[0],
                        "name": row[1],
                        "student_id": row[2],
                        "position": row[3],
                        "contact": row[4]
                    } for row in all_data[1:] if row[0]
                ]
            st.session_state[f"grp_{group_id}_members"] = members

        # 收入表同步
        earnings_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name=f"Group{group_id}Earnings"
        )
        if earnings_sheet:
            all_data = earnings_sheet.get_all_values()
            expected_headers = ["uuid", "date", "amount", "description", "handler"]
            
            if not all_data or all_data[0] != expected_headers:
                earnings_sheet.clear()
                earnings_sheet.append_row(expected_headers)
                earnings = []
            else:
                earnings = [
                    {
                        "uuid": row[0],
                        "date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "amount": float(row[2]),
                        "description": row[3],
                        "handler": row[4]
                    } for row in all_data[1:] if row[0]
                ]
            st.session_state[f"grp_{group_id}_earnings"] = earnings

    except Exception as e:
        st.warning(f"组 {group_id} 数据同步失败: {str(e)}")

def render_group_tab(group_id, sheet_handler):
    """渲染单个组的选项卡内容"""
    st.subheader(f"Group {group_id} Details")
    st.divider()

    # 确保数据已同步
    sync_group_data(sheet_handler, group_id)

    # 1. 小组成员名单部分
    st.markdown("### 👥 Group Members")
    
    # 成员列表展示
    members = st.session_state[f"grp_{group_id}_members"]
    if not members:
        st.info("No members in this group yet")
    else:
        col_widths = [0.5, 2, 2, 2, 2, 1]
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Name**")
        with header_cols[2]:
            st.write("**Student ID**")
        with header_cols[3]:
            st.write("**Position**")
        with header_cols[4]:
            st.write("**Contact**")
        with header_cols[5]:
            st.write("**Action**")
        
        st.markdown("---")
        scroll_container = st.container(height=200)
        with scroll_container:
            for idx, member in enumerate(members, 1):
                cols = st.columns(col_widths)
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(member["name"])
                with cols[2]:
                    st.write(member["student_id"])
                with cols[3]:
                    st.write(member["position"])
                with cols[4]:
                    st.write(member["contact"])
                with cols[5]:
                    if st.button(
                        "🗑️", 
                        key=f"grp_{group_id}_del_mem_{member['uuid']}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        # 删除本地数据
                        st.session_state[f"grp_{group_id}_members"].pop(idx - 1)
                        # 同步到Google Sheets
                        if sheet_handler:
                            try:
                                members_sheet = sheet_handler.get_worksheet(
                                    spreadsheet_name="Student",
                                    worksheet_name=f"Group{group_id}Members"
                                )
                                if members_sheet:
                                    cell = members_sheet.find(member["uuid"])
                                    if cell:
                                        members_sheet.delete_rows(cell.row)
                                st.success("Member deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"删除同步失败: {str(e)}")
                st.markdown("---")

    # 添加成员表单
    with st.expander("Add New Member", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", key=f"grp_{group_id}_add_name").strip()
            student_id = st.text_input("Student ID", key=f"grp_{group_id}_add_id").strip()
        with col2:
            position = st.text_input("Position", key=f"grp_{group_id}_add_pos").strip()
            contact = st.text_input("Contact", key=f"grp_{group_id}_add_cont").strip()
        
        if st.button("Add Member", key=f"grp_{group_id}_add_mem_btn", use_container_width=True):
            if not all([name, student_id, position]):
                st.error("Name, Student ID and Position are required!")
                return
            
            # 检查重复
            if any(m["student_id"] == student_id for m in members):
                st.error("Student ID already exists!")
                return
            
            # 创建新成员
            new_member = {
                "uuid": str(uuid.uuid4()),
                "name": name,
                "student_id": student_id,
                "position": position,
                "contact": contact
            }
            
            # 更新本地状态
            st.session_state[f"grp_{group_id}_members"].append(new_member)
            
            # 同步到Google Sheets
            if sheet_handler:
                try:
                    members_sheet = sheet_handler.get_worksheet(
                        spreadsheet_name="Student",
                        worksheet_name=f"Group{group_id}Members"
                    )
                    if members_sheet:
                        members_sheet.append_row([
                            new_member["uuid"],
                            new_member["name"],
                            new_member["student_id"],
                            new_member["position"],
                            new_member["contact"]
                        ])
                    st.success("Member added successfully!")
                    st.rerun()
                except Exception as e:
                    st.warning(f"添加同步失败: {str(e)}")

    st.divider()

    # 2. Group Earning部分
    st.markdown("### 💰 Group Earnings")
    
    # 收入记录展示
    earnings = st.session_state[f"grp_{group_id}_earnings"]
    if not earnings:
        st.info("No earnings recorded yet")
    else:
        col_widths = [0.5, 1.5, 1.5, 1.5, 3, 1.5, 1]
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Date**")
        with header_cols[2]:
            st.write("**Amount ($)**")
        with header_cols[3]:
            st.write("**Type**")
        with header_cols[4]:
            st.write("**Description**")
        with header_cols[5]:
            st.write("**Handled By**")
        with header_cols[6]:
            st.write("**Action**")
        
        st.markdown("---")
        scroll_container = st.container(height=200)
        with scroll_container:
            for idx, earning in enumerate(earnings, 1):
                cols = st.columns(col_widths)
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(earning["date"].strftime("%Y-%m-%d"))
                with cols[2]:
                    st.write(f"${earning['amount']:.2f}")
                with cols[3]:
                    st.write("Income")  # 收入类型固定为Income
                with cols[4]:
                    st.write(earning["description"])
                with cols[5]:
                    st.write(earning["handler"])
                with cols[6]:
                    if st.button(
                        "🗑️", 
                        key=f"grp_{group_id}_del_earn_{earning['uuid']}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        # 删除本地数据
                        st.session_state[f"grp_{group_id}_earnings"].pop(idx - 1)
                        # 同步到Google Sheets
                        if sheet_handler:
                            try:
                                earnings_sheet = sheet_handler.get_worksheet(
                                    spreadsheet_name="Student",
                                    worksheet_name=f"Group{group_id}Earnings"
                                )
                                if earnings_sheet:
                                    cell = earnings_sheet.find(earning["uuid"])
                                    if cell:
                                        earnings_sheet.delete_rows(cell.row)
                                st.success("Earning deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"删除同步失败: {str(e)}")
                st.markdown("---")

        # 收入汇总
        total_earnings = sum(e["amount"] for e in earnings)
        st.markdown(f"""
        <div style='padding: 0.5rem; background-color: #f8f9fa; border-radius: 8px;'>
            <strong>Total Earnings: ${total_earnings:.2f}</strong>
        </div>
        """, unsafe_allow_html=True)

    # 添加收入表单
    with st.expander("Add New Earning", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            earn_date = st.date_input(
                "Date", 
                value=datetime.today(),
                key=f"grp_{group_id}_earn_date"
            )
            amount = st.number_input(
                "Amount ($)", 
                min_value=0.01, 
                step=10.00, 
                value=100.00,
                key=f"grp_{group_id}_earn_amt"
            )
        with col2:
            description = st.text_input(
                "Description", 
                value="Fundraiser proceeds",
                key=f"grp_{group_id}_earn_desc"
            ).strip()
            handler = st.text_input(
                "Handled By", 
                value="",
                key=f"grp_{group_id}_earn_handler"
            ).strip()
        
        if st.button("Record Earning", key=f"grp_{group_id}_add_earn_btn", use_container_width=True):
            if not all([description, handler]):
                st.error("Description and Handled By are required!")
                return
            
            # 创建新收入记录
            new_earning = {
                "uuid": str(uuid.uuid4()),
                "date": earn_date,
                "amount": round(amount, 2),
                "description": description,
                "handler": handler
            }
            
            # 更新本地状态
            st.session_state[f"grp_{group_id}_earnings"].append(new_earning)
            
            # 同步到Google Sheets
            if sheet_handler:
                try:
                    earnings_sheet = sheet_handler.get_worksheet(
                        spreadsheet_name="Student",
                        worksheet_name=f"Group{group_id}Earnings"
                    )
                    if earnings_sheet:
                        earnings_sheet.append_row([
                            new_earning["uuid"],
                            new_earning["date"].strftime("%Y-%m-%d"),
                            str(new_earning["amount"]),
                            new_earning["description"],
                            new_earning["handler"]
                        ])
                    st.success("Earning recorded successfully!")
                    st.rerun()
                except Exception as e:
                    st.warning(f"记录同步失败: {str(e)}")

    st.divider()

    # 3. Reimbursement Requests部分（预留）
    st.markdown("### 📋 Reimbursement Requests")
    st.info("Reimbursement functionality will be added soon")

def render_groups():
    """渲染群组模块界面（grp_前缀命名空间）"""
    st.header("👥 Groups Management")
    st.write("Manage group members, earnings and reimbursement requests")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = init_google_sheet()

    # 创建8个组的选项卡
    group_tabs = st.tabs([f"Group {i}" for i in range(1, 9)])
    
    # 为每个选项卡渲染内容
    for i, tab in enumerate(group_tabs, 1):
        with tab:
            render_group_tab(str(i), sheet_handler)
