# modules/groups.py
import streamlit as st
import pandas as pd
import sys
import os
# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_groups():
    """渲染群组模块界面（grp_前缀命名空间），支持Google Sheets同步"""
    st.header("👥 Groups Management")
    st.write("Import and manage group and member data")
    st.divider()

    # ---------------------- 初始化Google Sheets连接 ----------------------
    sheet_handler = None
    groups_sheet = None  # 存储群组数据的工作表
    members_sheet = None  # 存储成员数据的工作表
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        # 获取或创建工作表
        groups_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Groups"
        )
        members_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Members"
        )
        # 若工作表不存在则创建并添加表头
        if not groups_sheet:
            groups_sheet = sheet_handler.create_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Groups",
                rows=100, cols=10
            )
            groups_sheet.append_row(["GroupID", "GroupName", "Leader", "Description", "MemberCount"])
        
        if not members_sheet:
            members_sheet = sheet_handler.create_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Members",
                rows=100, cols=10
            )
            members_sheet.append_row(["MemberID", "GroupID", "GroupName", "Name", "StudentID", "Position", "Contact"])
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # ---------------------- 从Google Sheets同步数据到本地 ----------------------
    def sync_from_sheets():
        """从Sheets同步群组和成员数据到本地会话状态"""
        if not (sheet_handler and groups_sheet and members_sheet):
            return
        
        # 同步群组数据
        try:
            groups_data = groups_sheet.get_all_values()
            expected_group_headers = ["GroupID", "GroupName", "Leader", "Description", "MemberCount"]
            if not groups_data or groups_data[0] != expected_group_headers:
                groups_sheet.clear()
                groups_sheet.append_row(expected_group_headers)
                st.session_state.grp_list = []
            else:
                st.session_state.grp_list = [
                    {
                        "GroupID": row[0],
                        "GroupName": row[1],
                        "Leader": row[2],
                        "Description": row[3],
                        "MemberCount": int(row[4]) if row[4].isdigit() else 0
                    } for row in groups_data[1:] if row[0]
                ]
        except Exception as e:
            st.warning(f"群组数据同步失败: {str(e)}")
        
        # 同步成员数据
        try:
            members_data = members_sheet.get_all_values()
            expected_member_headers = ["MemberID", "GroupID", "GroupName", "Name", "StudentID", "Position", "Contact"]
            if not members_data or members_data[0] != expected_member_headers:
                members_sheet.clear()
                members_sheet.append_row(expected_member_headers)
                st.session_state.grp_members = []
            else:
                st.session_state.grp_members = [
                    {
                        "MemberID": row[0],
                        "GroupID": row[1],
                        "GroupName": row[2],
                        "Name": row[3],
                        "StudentID": row[4],
                        "Position": row[5],
                        "Contact": row[6]
                    } for row in members_data[1:] if row[0]
                ]
        except Exception as e:
            st.warning(f"成员数据同步失败: {str(e)}")

    # 首次加载时同步数据
    if "grp_list" not in st.session_state or "grp_members" not in st.session_state:
        sync_from_sheets()
    # 初始化本地状态（防止空值错误）
    if "grp_list" not in st.session_state:
        st.session_state.grp_list = []
    if "grp_members" not in st.session_state:
        st.session_state.grp_members = []

    # ---------------------- 数据导入区域（支持同步到Sheets） ----------------------
    st.subheader("Import Data from File")
    st.write("Supported formats: .xlsx, .csv")
    
    import_type = st.radio(
        "Select data type to import",
        ["Groups", "Members"],
        key="grp_radio_import_type"
    )
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"],
        key="grp_upload_file"
    )
    
    if st.button("Import Data", key="grp_btn_import", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a file first!")
            return
        
        try:
            # 读取文件
            if uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            if import_type == "Groups":
                required_cols = ["GroupName", "Leader"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Groups file must contain columns: {', '.join(required_cols)}")
                    return
                
                added_count = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    leader = str(row["Leader"]).strip()
                    description = str(row.get("Description", "")).strip()
                    
                    if not group_name or not leader:
                        st.warning(f"Skipping invalid row: GroupName or Leader missing")
                        continue
                    
                    if any(g["GroupName"] == group_name for g in st.session_state.grp_list):
                        st.warning(f"Skipping duplicate group: {group_name}")
                        continue
                    
                    group_id = f"G{len(st.session_state.grp_list) + 1:03d}"
                    new_group = {
                        "GroupID": group_id,
                        "GroupName": group_name,
                        "Leader": leader,
                        "Description": description,
                        "MemberCount": 0
                    }
                    
                    # 更新本地状态
                    st.session_state.grp_list.append(new_group)
                    # 同步到Google Sheets
                    if groups_sheet:
                        groups_sheet.append_row([
                            new_group["GroupID"],
                            new_group["GroupName"],
                            new_group["Leader"],
                            new_group["Description"],
                            str(new_group["MemberCount"])
                        ])
                    added_count += 1
                
                st.success(f"Successfully imported {added_count} new groups!")
            
            else:  # 导入成员
                required_cols = ["GroupName", "Name", "StudentID", "Position"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Members file must contain columns: {', '.join(required_cols)}")
                    return
                
                if not st.session_state.grp_list:
                    st.error("No existing groups. Please create groups first.")
                    return
                
                added_count = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    member_name = str(row["Name"]).strip()
                    student_id = str(row["StudentID"]).strip()
                    position = str(row["Position"]).strip()
                    contact = str(row.get("Contact", "")).strip()
                    
                    if not all([group_name, member_name, student_id, position]):
                        st.warning(f"Skipping invalid row: Missing required fields")
                        continue
                    
                    group = next((g for g in st.session_state.grp_list if g["GroupName"] == group_name), None)
                    if not group:
                        st.warning(f"Skipping: Group '{group_name}' not found")
                        continue
                    
                    if any(
                        m["StudentID"] == student_id and m["GroupID"] == group["GroupID"]
                        for m in st.session_state.grp_members
                    ):
                        st.warning(f"Skipping duplicate member: {member_name} (StudentID: {student_id})")
                        continue
                    
                    member_id = f"M{len(st.session_state.grp_members) + 1:03d}"
                    new_member = {
                        "MemberID": member_id,
                        "GroupID": group["GroupID"],
                        "GroupName": group_name,
                        "Name": member_name,
                        "StudentID": student_id,
                        "Position": position,
                        "Contact": contact
                    }
                    
                    # 更新本地状态
                    st.session_state.grp_members.append(new_member)
                    group["MemberCount"] += 1  # 更新群组成员数
                    # 同步到Google Sheets
                    if members_sheet and groups_sheet:
                        members_sheet.append_row([
                            new_member["MemberID"],
                            new_member["GroupID"],
                            new_member["GroupName"],
                            new_member["Name"],
                            new_member["StudentID"],
                            new_member["Position"],
                            new_member["Contact"]
                        ])
                        # 更新群组的MemberCount
                        group_cell = groups_sheet.find(group["GroupID"])
                        if group_cell:
                            groups_sheet.update_cell(group_cell.row, 5, group["MemberCount"])
                    added_count += 1
                
                st.success(f"Successfully imported {added_count} new members!")
        
        except Exception as e:
            st.error(f"Import failed: {str(e)}")

    st.markdown("---")

    # ---------------------- 数据展示与删除功能（支持同步到Sheets） ----------------------
    # 1. 群组列表（带删除按钮）
    st.subheader("Groups List")
    if not st.session_state.grp_list:
        st.info("No groups found. Please import groups first.")
    else:
        # 显示表头
        col_widths = [1, 2, 2, 3, 1, 1]
        header_cols = st.columns(col_widths)
        header_cols[0].write("**Group ID**")
        header_cols[1].write("**Group Name**")
        header_cols[2].write("**Leader**")
        header_cols[3].write("**Description**")
        header_cols[4].write("**Member Count**")
        header_cols[5].write("**Action**")
        st.markdown("---")

        # 显示群组数据
        for idx, group in enumerate(st.session_state.grp_list):
            cols = st.columns(col_widths)
            cols[0].write(group["GroupID"])
            cols[1].write(group["GroupName"])
            cols[2].write(group["Leader"])
            cols[3].write(group["Description"])
            cols[4].write(group["MemberCount"])
            
            # 删除按钮
            if cols[5].button("🗑️ Delete", key=f"del_group_{group['GroupID']}", use_container_width=True):
                # 本地删除
                st.session_state.grp_list.pop(idx)
                # 删除关联成员
                st.session_state.grp_members = [
                    m for m in st.session_state.grp_members 
                    if m["GroupID"] != group["GroupID"]
                ]
                
                # 同步到Sheets
                if groups_sheet and members_sheet:
                    try:
                        # 删除群组行
                        group_cell = groups_sheet.find(group["GroupID"])
                        if group_cell:
                            groups_sheet.delete_rows(group_cell.row)
                        # 删除关联成员（倒序删除避免索引错乱）
                        member_ids = [m["MemberID"] for m in st.session_state.grp_members if m["GroupID"] == group["GroupID"]]
                        rows_to_delete = []
                        for mid in member_ids:
                            cell = members_sheet.find(mid)
                            if cell:
                                rows_to_delete.append(cell.row)
                        for row in sorted(rows_to_delete, reverse=True):
                            members_sheet.delete_rows(row)
                        st.success(f"Group {group['GroupName']} deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"同步删除失败: {str(e)}")

            st.markdown("---")

    # 2. 成员列表（带删除按钮）
    st.subheader("Group Members")
    if not st.session_state.grp_members:
        st.info("No members found. Please import members first.")
    else:
        # 显示表头
        col_widths = [1, 2, 2, 2, 2, 2, 1]
        header_cols = st.columns(col_widths)
        header_cols[0].write("**Member ID**")
        header_cols[1].write("**Group Name**")
        header_cols[2].write("**Name**")
        header_cols[3].write("**Student ID**")
        header_cols[4].write("**Position**")
        header_cols[5].write("**Contact**")
        header_cols[6].write("**Action**")
        st.markdown("---")

        # 显示成员数据
        for idx, member in enumerate(st.session_state.grp_members):
            cols = st.columns(col_widths)
            cols[0].write(member["MemberID"])
            cols[1].write(member["GroupName"])
            cols[2].write(member["Name"])
            cols[3].write(member["StudentID"])
            cols[4].write(member["Position"])
            cols[5].write(member["Contact"])
            
            # 删除按钮
            if cols[6].button("🗑️ Delete", key=f"del_member_{member['MemberID']}", use_container_width=True):
                # 本地删除
                deleted_member = st.session_state.grp_members.pop(idx)
                # 更新群组成员数
                group = next(g for g in st.session_state.grp_list if g["GroupID"] == deleted_member["GroupID"])
                group["MemberCount"] -= 1
                
                # 同步到Sheets
                if members_sheet and groups_sheet:
                    try:
                        # 删除成员行
                        member_cell = members_sheet.find(deleted_member["MemberID"])
                        if member_cell:
                            members_sheet.delete_rows(member_cell.row)
                        # 更新群组成员数
                        group_cell = groups_sheet.find(group["GroupID"])
                        if group_cell:
                            groups_sheet.update_cell(group_cell.row, 5, group["MemberCount"])
                        st.success(f"Member {deleted_member['Name']} deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"同步删除失败: {str(e)}")

            st.markdown("---")
