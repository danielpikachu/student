# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_attendance():
    """渲染考勤模块界面（确保操作一次生效）"""
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # 初始化Google Sheets连接
    sheet_handler = None
    attendance_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        attendance_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Attendance"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 初始化会话状态（确保存在）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    # 用于标记是否需要立即刷新表格
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 核心修复：直接更新本地状态并立即刷新表格（不依赖Google Sheets同步延迟）
    def add_meeting_directly(meeting_name):
        # 生成新会议ID
        new_meeting_id = len(st.session_state.att_meetings) + 1
        # 1. 先更新本地会话状态（立即生效）
        st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
        
        # 2. 为每个成员添加默认缺勤记录（本地）
        for member in st.session_state.att_members:
            st.session_state.att_records[(member["id"], new_meeting_id)] = False
        
        # 3. 同步到Google Sheets（后台操作，不阻塞UI）
        if attendance_sheet and sheet_handler:
            try:
                for member in st.session_state.att_members:
                    attendance_sheet.append_row([
                        str(member["id"]),
                        member["name"],
                        str(new_meeting_id),
                        meeting_name,
                        "FALSE",  # 默认缺勤
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
            except Exception as e:
                st.warning(f"Google Sheets同步延迟: {str(e)}")
        
        # 标记需要刷新表格
        st.session_state.att_needs_refresh = True

    # 从Google Sheets同步数据（仅用于初始加载和后台同步）
    def sync_from_sheets():
        if not attendance_sheet or not sheet_handler:
            return
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data:
                return
                
            headers = all_data[0]
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                return

            # 提取会议数据
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if row[2] and row[3] and row[2] not in meeting_ids:
                    meeting_ids.add(row[2])
                    meetings.append({"id": int(row[2]), "name": row[3]})
            
            # 提取成员数据
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if row[0] and row[1] and row[0] not in member_ids:
                    member_ids.add(row[0])
                    members.append({"id": int(row[0]), "name": row[1]})
            
            # 提取考勤记录
            records = {}
            for row in all_data[1:]:
                if row[0] and row[2]:
                    member_id = int(row[0])
                    meeting_id = int(row[2])
                    records[(member_id, meeting_id)] = row[4].lower() == "true"
            
            # 仅在本地状态为空时初始化（避免覆盖用户刚添加的数据）
            if not st.session_state.att_meetings:
                st.session_state.att_meetings = meetings
            if not st.session_state.att_members:
                st.session_state.att_members = members
            if not st.session_state.att_records:
                st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"后台同步忽略: {str(e)}")

    # 初始同步（仅一次）
    if not st.session_state.att_meetings or not st.session_state.att_members:
        sync_from_sheets()

    # ---------------------- 考勤表格展示（关键：使用本地状态直接渲染） ----------------------
    def render_attendance_table():
        if st.session_state.att_members and st.session_state.att_meetings:
            data = []
            for member in st.session_state.att_members:
                row = {"Member Name": member["name"]}
                # 直接从本地状态读取最新会议数据
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                # 计算出勤率
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                data.append(row)
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No members or meetings found. Please add data first.")

    # 渲染表格（始终使用最新本地状态）
    render_attendance_table()

    st.markdown("---")

    # ---------------------- 操作区域布局 ----------------------
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    # 左侧：成员导入 + 会议管理
    with col_left:
        # 1. 导入成员
        with st.container(border=True):
            st.subheader("Import Members")
            if st.button("Import from members.xlsx", key="att_import_members"):
                try:
                    df = pd.read_excel("members.xlsx")
                    if "Member Name" not in df.columns:
                        st.error("Excel must have 'Member Name' column!")
                        return
                    
                    new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                    added = 0
                    for name in new_members:
                        if not any(m["name"] == name for m in st.session_state.att_members):
                            new_id = len(st.session_state.att_members) + 1
                            st.session_state.att_members.append({"id": new_id, "name": name})
                            # 为现有会议添加默认记录
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                            added += 1
                    
                    st.success(f"Added {added} new members")
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # 2. 会议管理（添加/删除）
        with st.container(border=True):
            st.subheader("Manage Meetings")
            # 添加会议（核心修复区域）
            meeting_name = st.text_input(
                "Enter meeting name", 
                placeholder="e.g., Weekly Sync",
                key="att_meeting_name"
            )
            
            if st.button("Add Meeting", key="att_add_meeting"):
                meeting_name = meeting_name.strip()
                if not meeting_name:
                    st.error("Please enter a meeting name")
                    return
                if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                    st.error("Meeting already exists")
                    return
                
                # 直接添加到本地状态并刷新表格（一次点击生效）
                add_meeting_directly(meeting_name)
                st.success(f"Added meeting: {meeting_name}")

            # 删除会议
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "Select meeting to delete",
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_del_meeting"
                )
                
                if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                    # 1. 更新本地状态
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    # 2. 同步到Google Sheets
                    if attendance_sheet and sheet_handler:
                        try:
                            rows = attendance_sheet.get_all_values()
                            for i in range(len(rows)-1, 0, -1):
                                if rows[i][2] == str(selected_meeting["id"]):
                                    attendance_sheet.delete_rows(i+1)
                        except Exception as e:
                            st.warning(f"Delete sync failed: {str(e)}")
                    
                    st.success(f"Deleted meeting: {selected_meeting['name']}")
                    st.session_state.att_needs_refresh = True

    # 右侧：更新考勤
    with col_right.container(border=True):
        st.subheader("Update Attendance")
        
        if st.session_state.att_meetings:
            selected_meeting = st.selectbox(
                "Select Meeting", 
                st.session_state.att_meetings,
                format_func=lambda x: x["name"],
                key="att_update_meeting"
            )
            
            # 一键全到
            if st.button("Set All Present", key="att_set_all"):
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                
                # 同步到Sheets
                if attendance_sheet and sheet_handler:
                    try:
                        rows = attendance_sheet.get_all_values()
                        for member in st.session_state.att_members:
                            for i, row in enumerate(rows[1:], start=2):
                                if row[0] == str(member["id"]) and row[2] == str(selected_meeting["id"]):
                                    attendance_sheet.delete_rows(i)
                            attendance_sheet.append_row([
                                str(member["id"]), member["name"],
                                str(selected_meeting["id"]), selected_meeting["name"],
                                "TRUE", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                    except Exception as e:
                        st.warning(f"Sync warning: {str(e)}")
                
                st.success(f"All present for {selected_meeting['name']}")
                st.session_state.att_needs_refresh = True

        # 单独更新成员状态
        if st.session_state.att_members and st.session_state.att_meetings:
            selected_member = st.selectbox(
                "Select Member",
                st.session_state.att_members,
                format_func=lambda x: x["name"],
                key="att_update_member"
            )
            
            current_status = st.session_state.att_records.get((selected_member["id"], selected_meeting["id"]), False)
            is_present = st.checkbox("Present", value=current_status, key="att_is_present")
            
            if st.button("Save Attendance", key="att_save_attendance"):
                st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = is_present
                
                # 同步到Sheets
                if attendance_sheet and sheet_handler:
                    try:
                        rows = attendance_sheet.get_all_values()
                        for i, row in enumerate(rows[1:], start=2):
                            if row[0] == str(selected_member["id"]) and row[2] == str(selected_meeting["id"]):
                                attendance_sheet.delete_rows(i)
                        attendance_sheet.append_row([
                            str(selected_member["id"]), selected_member["name"],
                            str(selected_meeting["id"]), selected_meeting["name"],
                            "TRUE" if is_present else "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                    except Exception as e:
                        st.warning(f"Sync warning: {str(e)}")
                
                st.success(f"Updated {selected_member['name']}'s status")
                st.session_state.att_needs_refresh = True

    # 如果需要刷新，强制重新渲染表格（关键修复）
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        # 重新渲染表格（使用最新的本地状态）
        render_attendance_table()
