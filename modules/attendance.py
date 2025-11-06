# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import time

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 处理Google API错误
try:
    from googleapiclient.errors import HttpError
except ImportError:
    class HttpError(Exception):
        def __init__(self, resp, content, uri=None):
            self.resp = resp
            self.content = content
            self.uri = uri

def render_attendance():
    """保持界面不变，仅同步数据格式到Google Sheet"""
    # 界面布局完全不变
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # 初始化Google Sheets连接
    sheet_handler = None
    attendance_sheet = None
    sheet_available = False
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        # 尝试获取工作表
        try:
            attendance_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Attendance"
            )
            sheet_available = True
        except:
            # 不提示创建信息，避免界面干扰
            pass
    except:
        # 静默失败，不显示错误干扰界面
        pass

    # 初始化会话状态（保持原样）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 核心同步函数：仅同步数据，不改变界面
    def sync_to_sheet_silently():
        """静默同步数据到Google Sheet，不显示额外提示"""
        if not sheet_available or not attendance_sheet:
            return

        try:
            # 1. 准备与界面表格完全一致的数据
            # 表头：成员名 + 会议名 + 出勤率
            headers = ["Member Name"] + [m["name"] for m in st.session_state.att_meetings] + ["Attendance Rates"]
            
            # 表格内容
            rows = []
            for member in st.session_state.att_members:
                row = [member["name"]]
                # 各会议出勤状态（✓/✗）
                for meeting in st.session_state.att_meetings:
                    row.append("✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗")
                # 出勤率
                attended = sum(1 for m in st.session_state.att_meetings if st.session_state.att_records.get((member["id"], m["id"]), False))
                total = len(st.session_state.att_meetings)
                row.append(f"{(attended/total*100):.1f}%" if total > 0 else "0%")
                rows.append(row)

            # 2. 清空并写入新数据（确保格式一致）
            attendance_sheet.clear()
            attendance_sheet.append_row(headers)
            if rows:
                attendance_sheet.append_rows(rows)
                # 设置表头加粗（不影响界面）
                attendance_sheet.format("1:1", {"textFormat": {"bold": True}})

        except:
            # 同步失败不提示，避免干扰界面
            pass

    # 从Sheet加载数据（不影响界面）
    def load_from_sheet_silently():
        """静默从Sheet加载数据，仅在首次启动时执行"""
        if not sheet_available or not attendance_sheet or (st.session_state.att_members or st.session_state.att_meetings):
            return

        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data or len(all_data) < 2:
                return

            headers = all_data[0]
            if headers[0] != "Member Name":
                return

            # 提取会议
            meetings = headers[1:-1] if len(headers) > 2 else []
            st.session_state.att_meetings = [{"id": i+1, "name": name} for i, name in enumerate(meetings)]

            # 提取成员和记录
            members = []
            records = {}
            for row in all_data[1:]:
                if not row or not row[0]:
                    continue
                member_id = len(members) + 1
                members.append({"id": member_id, "name": row[0].strip()})
                for i, meeting in enumerate(st.session_state.att_meetings):
                    if i+1 < len(row):
                        records[(member_id, meeting["id"])] = (row[i+1].strip() == "✓")

            st.session_state.att_members = members
            st.session_state.att_records = records
        except:
            pass

    # 初始加载（不影响界面）
    load_from_sheet_silently()

    # 渲染考勤表格（完全保持原界面）
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

    # 操作区域（完全保持原界面布局和功能）
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    with col_left:
        # 1. 导入成员（保持原界面）
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
                    sync_to_sheet_silently()  # 仅添加同步逻辑
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # 2. 会议管理（保持原界面）
        with st.container(border=True):
            st.subheader("Manage Meetings")
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
                
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                sync_to_sheet_silently()  # 仅添加同步逻辑
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
                    sync_to_sheet_silently()  # 仅添加同步逻辑
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
                sync_to_sheet_silently()  # 仅添加同步逻辑
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
                sync_to_sheet_silently()  # 仅添加同步逻辑
                st.session_state.att_needs_refresh = True

    # 刷新逻辑（保持不变）
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
