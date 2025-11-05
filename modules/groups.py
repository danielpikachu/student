import streamlit as st
import sys
import os
from datetime import datetime
import uuid

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入工具类
from google_sheet_utils import GoogleSheetHandler

def render_groups():
    # 为当前模块生成唯一标识（可选，进一步增强唯一性）
    module_prefix = "groups_"  # 模块专属前缀，核心是这个
    
    # 初始化会话状态
    if 'groups' not in st.session_state:
        st.session_state.groups = []
    if 'group_members' not in st.session_state:
        st.session_state.group_members = []
    
    # 初始化Google Sheets连接
    sheet_handler = None
    groups_sheet = None
    members_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        groups_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Groups"
        )
        members_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="GroupMembers"
        )
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")

    # 数据导入选项（关键修改：添加模块前缀）
    import_type = st.radio(
        "Select data type to import",
        ["Groups", "Members"],
        key=f"{module_prefix}import_type_radio"  # 确保与其他模块不冲突
    )

    # 同步数据按钮（添加模块前缀）
    if st.button("Sync from Google Sheets", key=f"{module_prefix}sync_btn"):
        if import_type == "Groups" and groups_sheet:
            try:
                data = groups_sheet.get_all_values()
                if data and len(data) > 1:
                    st.session_state.groups = [
                        {"id": row[0], "name": row[1], "created": row[2]}
                        for row in data[1:] if row
                    ]
                    st.success(f"Synced {len(st.session_state.groups)} groups")
            except Exception as e:
                st.error(f"同步Groups失败: {str(e)}")
        
        elif import_type == "Members" and members_sheet:
            try:
                data = members_sheet.get_all_values()
                if data and len(data) > 1:
                    st.session_state.group_members = [
                        {"group_id": row[0], "member_name": row[1], "role": row[2]}
                        for row in data[1:] if row
                    ]
                    st.success(f"Synced {len(st.session_state.group_members)} members")
            except Exception as e:
                st.error(f"同步Members失败: {str(e)}")

    # 显示Groups数据
    if import_type == "Groups":
        st.subheader("Groups List")
        if not st.session_state.groups:
            st.info("No groups data available. Click 'Sync' to load.")
        else:
            for idx, group in enumerate(st.session_state.groups):
                # 每个小组的删除按钮（添加模块前缀+唯一ID）
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"**{group['name']}** (ID: {group['id']}, Created: {group['created']})")
                if col2.button(
                    "Delete",
                    key=f"{module_prefix}del_group_{group['id']}_{idx}",  # 多重唯一保障
                    use_container_width=True
                ):
                    st.session_state.groups = [g for g in st.session_state.groups if g["id"] != group["id"]]
                    st.success(f"Group {group['name']} deleted")
                    st.rerun()

    # 显示Members数据
    else:
        st.subheader("Group Members")
        if not st.session_state.group_members:
            st.info("No members data available. Click 'Sync' to load.")
        else:
            for idx, member in enumerate(st.session_state.group_members):
                # 每个成员的删除按钮（添加模块前缀+唯一ID）
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"**{member['member_name']}** (Group: {member['group_id']}, Role: {member['role']})")
                if col2.button(
                    "Delete",
                    key=f"{module_prefix}del_member_{member['group_id']}_{idx}_{uuid.uuid4().hex[:4]}",  # 极端唯一
                    use_container_width=True
                ):
                    st.session_state.group_members = [m for m in st.session_state.group_members if 
                                                     m["group_id"] != member["group_id"] or 
                                                     m["member_name"] != member["member_name"]]
                    st.success(f"Member {member['member_name']} deleted")
                    st.rerun()

    # 新增数据区域（所有key都加模块前缀）
    st.subheader("Add New Entry")
    with st.form(key=f"{module_prefix}new_entry_form"):
        if import_type == "Groups":
            group_id = st.text_input("Group ID", key=f"{module_prefix}new_group_id")
            group_name = st.text_input("Group Name", key=f"{module_prefix}new_group_name")
            created_date = st.date_input("Created Date", value=datetime.today(), key=f"{module_prefix}new_group_date")
        else:
            member_group_id = st.text_input("Group ID", key=f"{module_prefix}new_member_group_id")
            member_name = st.text_input("Member Name", key=f"{module_prefix}new_member_name")
            member_role = st.text_input("Role", key=f"{module_prefix}new_member_role")
        
        submit = st.form_submit_button("Add Entry", key=f"{module_prefix}add_entry_btn")
        
        if submit:
            if import_type == "Groups" and group_id and group_name:
                new_group = {
                    "id": group_id,
                    "name": group_name,
                    "created": created_date.strftime("%Y-%m-%d")
                }
                st.session_state.groups.append(new_group)
                if groups_sheet:
                    groups_sheet.append_row([group_id, group_name, created_date.strftime("%Y-%m-%d")])
                st.success("Group added successfully")
                st.rerun()
            elif import_type == "Members" and member_group_id and member_name:
                new_member = {
                    "group_id": member_group_id,
                    "member_name": member_name,
                    "role": member_role or "Member"
                }
                st.session_state.group_members.append(new_member)
                if members_sheet:
                    members_sheet.append_row([member_group_id, member_name, member_role or "Member"])
                st.success("Member added successfully")
                st.rerun()
            else:
                st.error("Required fields cannot be empty!")
