# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 解决根目录导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_attendance():
    # 界面设置（完全不变）
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # 初始化Google Sheets连接（简化版）
    sheet_handler = None
    attendance_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        attendance_sheet = sheet_handler.get_worksheet("Student", "Attendance")
    except:
        pass  # 连接失败不提示，避免影响界面

    # 会话状态初始化（与原界面一致）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 核心：同步表格到Google Sheet（仅做这件事，不影响界面）
    def sync_to_sheet():
        if not attendance_sheet:
            return

        # 1. 准备与界面完全相同的表格数据
        # 表头：成员名 + 所有会议名 + 出勤率
        headers = ["Member Name"]
        for meeting in st.session_state.att_meetings:
            headers.append(meeting["name"])
        headers.append("Attendance Rates")

        # 表格内容
        rows = []
        for member in st.session_state.att_members:
            row = [member["name"]]
            # 各会议出勤状态（✓/✗）
            for meeting in st.session_state.att_meetings:
                row.append("✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗")
            # 出勤率计算
            attended = sum(1 for m in st.session_state.att_meetings if st.session_state.att_records.get((member["id"], m["id"]), False))
            total = len(st.session_state.att_meetings)
            row.append(f"{(attended/total*100):.1f}%" if total > 0 else "0%")
            rows.append(row)

        # 2. 写入Google Sheet（先清空再写入，确保一致）
        try:
            attendance_sheet.clear()  # 清空旧数据
            attendance_sheet.append_row(headers)  # 写入表头
            if rows:
                attendance_sheet.append_rows(rows)  # 写入内容
                attendance_sheet.format("1:1", {"textFormat": {"bold": True}})  # 表头加粗
        except:
            pass  # 同步失败不影响界面

    # 渲染考勤表格（与原界面完全一致）
    def render_attendance_table():
        if st.session_state.att_members and st.session_state.att_meetings:
            data = []
            for member in st.session_state.att_members:
                row = {"Member Name": member["name"]}
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                attended = sum(1 for m in st.session_state.att_meetings if st.session_state.att_records.get((member["id"], m["id"]), False))
                total = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended/total*100):.1f}%" if total > 0 else "0%"
                data.append(row)
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No members or meetings found. Please add data first.")

    # 渲染表格（界面不变）
    render_attendance_table()

    st.markdown("---")

    # 操作区域（与原界面完全一致）
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    with col_left:
        # 1. 导入成员（原界面逻辑）
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
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                            added += 1
                    st.success(f"Added {added} new members")
                    sync_to_sheet()  # 同步到Sheet
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # 2. 会议管理（原界面逻辑）
        with st.container(border=True):
            st.subheader("Manage Meetings")
            meeting_name = st.text_input("Enter meeting name", placeholder="e.g., Weekly Sync", key="att_meeting_name")
            
            if st.button("Add Meeting", key="att_add_meeting"):
                meeting_name = meeting_name.strip()
                if not meeting_name:
                    st.error("Please enter a meeting name")
                    return
                if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                    st.error("Meeting already exists")
                    return
                
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                sync_to_sheet()  # 同步到Sheet
                st.session_state.att_needs_refresh = True

            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "Select meeting to delete",
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_del_meeting"
                )
                
                if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    st.success(f"Deleted meeting: {selected_meeting['name']}")
                    sync_to_sheet()  # 同步到Sheet
                    st.session_state.att_needs_refresh = True

    with col_right.container(border=True):
        st.subheader("Update Attendance")
        
        if st.session_state.att_meetings:
            selected_meeting = st.selectbox(
                "Select Meeting", 
                st.session_state.att_meetings,
                format_func=lambda x: x["name"],
                key="att_update_meeting"
            )
            
            if st.button("Set All Present", key="att_set_all"):
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                
                st.success(f"All present for {selected_meeting['name']}")
                sync_to_sheet()  # 同步到Sheet
                st.session_state.att_needs_refresh = True

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
                
                st.success(f"Updated {selected_member['name']}'s status")
                sync_to_sheet()  # 同步到Sheet
                st.session_state.att_needs_refresh = True

    # 刷新逻辑（保持不变）
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
