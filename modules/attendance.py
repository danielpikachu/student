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
    """渲染考勤模块界面，修复空状态下考勤表不显示的问题"""
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

    # 初始化会话状态（确保基础结构存在）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 全量更新Google Sheets数据（覆盖方式）
    def full_update_sheets(max_retries=3):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 准备表头
                rows = [["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]]
                
                # 准备所有考勤记录（即使没有会议或成员也生成表头）
                for member in st.session_state.att_members:
                    # 如果没有会议，仍然保留成员记录（关联空会议）
                    if st.session_state.att_meetings:
                        for meeting in st.session_state.att_meetings:
                            is_present = st.session_state.att_records.get((member["id"], meeting["id"]), False)
                            rows.append([
                                str(member["id"]),
                                member["name"],
                                str(meeting["id"]),
                                meeting["name"],
                                "TRUE" if is_present else "FALSE",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                    else:
                        # 没有会议时也要保留成员数据
                        rows.append([
                            str(member["id"]),
                            member["name"],
                            "", "", "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                
                # 清除现有内容并写入新数据
                attendance_sheet.clear()
                attendance_sheet.append_rows(rows, value_input_option='RAW')
                return True
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 5))
                    st.warning(f"请求频率超限，将在 {retry_after} 秒后重试...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"更新失败: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"更新失败: {str(e)}")
                return False
        
        st.error("达到最大重试次数，同步失败")
        return False

    # 从Google Sheets同步数据
    def sync_from_sheets():
        if not attendance_sheet or not sheet_handler:
            return
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data:
                return
                
            headers = all_data[0] if len(all_data) > 0 else []
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                return

            # 提取会议数据
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if len(row) >= 4 and row[2] and row[3] and row[2] not in meeting_ids:
                    meeting_ids.add(row[2])
                    try:
                        meetings.append({"id": int(row[2]), "name": row[3]})
                    except (ValueError, IndexError):
                        continue  # 跳过格式错误的行
            
            # 提取成员数据
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if len(row) >= 2 and row[0] and row[1] and row[0] not in member_ids:
                    member_ids.add(row[0])
                    try:
                        members.append({"id": int(row[0]), "name": row[1]})
                    except (ValueError, IndexError):
                        continue  # 跳过格式错误的行
            
            # 提取考勤记录
            records = {}
            for row in all_data[1:]:
                if len(row) >= 5 and row[0] and row[2]:
                    try:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        records[(member_id, meeting_id)] = row[4].lower() == "true"
                    except (ValueError, IndexError):
                        continue  # 跳过格式错误的行
            
            # 更新本地状态
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"同步失败: {str(e)}")

    # 初始同步（即使已有数据也强制同步一次，确保状态一致）
    sync_from_sheets()

    # 渲染考勤表格（修复空状态处理）
    def render_attendance_table():
        # 即使只有成员或只有会议，也显示表格
        if st.session_state.att_members or st.session_state.att_meetings:
            data = []
            # 如果没有成员，创建一个占位行
            members_to_render = st.session_state.att_members if st.session_state.att_members else [{"id": 0, "name": "No members"}]
            
            for member in members_to_render:
                row = {"Member Name": member["name"]}
                # 处理没有会议的情况
                if st.session_state.att_meetings:
                    for meeting in st.session_state.att_meetings:
                        row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                    
                    # 计算出勤率
                    attended_count = sum(1 for m in st.session_state.att_meetings 
                                       if st.session_state.att_records.get((member["id"], m["id"]), False))
                    total_meetings = len(st.session_state.att_meetings)
                    row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                else:
                    row["Status"] = "No meetings created yet"
                    row["Attendance Rates"] = "N/A"
                
                data.append(row)
            
            with st.container():
                st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No members or meetings found. Please add data first.")

    # 渲染表格（确保始终执行）
    render_attendance_table()

    st.markdown("---")

    # 操作区域布局
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
                            # 为现有会议添加默认记录（本地）
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                            added += 1
                    
                    st.success(f"Added {added} new members")
                    # 全量更新到Sheets
                    if not full_update_sheets():
                        st.warning("数据同步失败，请稍后重试")
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # 2. 会议管理
        with st.container(border=True):
            st.subheader("Manage Meetings")
            # 添加会议
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
                # 更新本地状态
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                
                # 为每个成员添加默认缺勤记录（本地）- 修复：即使没有成员也执行此操作
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                # 全量更新到Sheets
                if not full_update_sheets():
                    st.warning("数据同步失败，请稍后重试")
                st.session_state.att_needs_refresh = True

            # 删除会议
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "Select meeting to delete",
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_del_meeting"
                )
                
                if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                    # 更新本地状态
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    st.success(f"Deleted meeting: {selected_meeting['name']}")
                    # 全量更新到Sheets
                    if not full_update_sheets():
                        st.warning("数据同步失败，请稍后重试")
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
                # 更新本地状态
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                
                st.success(f"All present for {selected_meeting['name']}")
                # 全量更新到Sheets
                if not full_update_sheets():
                    st.warning("数据同步失败，请稍后重试")
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
                # 更新本地状态
                st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = is_present
                
                st.success(f"Updated {selected_member['name']}'s status")
                # 全量更新到Sheets
                if not full_update_sheets():
                    st.warning("数据同步失败，请稍后重试")
                st.session_state.att_needs_refresh = True

    # 刷新页面（确保状态变更后重新渲染）
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
