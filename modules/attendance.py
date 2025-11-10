# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time

# Resolve root directory module import issue
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import Google Sheets utility class
from google_sheet_utils import GoogleSheetHandler

# Handle Google API errors
try:
    from googleapiclient.errors import HttpError
except ImportError:
    class HttpError(Exception):
        def __init__(self, resp, content, uri=None):
            self.resp = resp
            self.content = content
            self.uri = uri

def render_attendance():
    """Render attendance module interface, ensuring Google Sheet and interface are completely consistent"""
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # Initialize Google Sheets connection
    sheet_handler = None
    attendance_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        attendance_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Attendance"
        )
    except Exception as e:
        st.error(f"Google Sheets initialization failed: {str(e)}")

    # Initialize session state
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = None
    if "att_batch_updates" not in st.session_state:
        st.session_state.att_batch_updates = []
    if "has_pending_updates" not in st.session_state:
        st.session_state.has_pending_updates = False

    # Full update Google Sheets data (overwrite mode)
    def full_update_sheets(max_retries=3):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Prepare header
                rows = [["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]]
                
                # Prepare all attendance records
                for member in st.session_state.att_members:
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
                        rows.append([
                            str(member["id"]),
                            member["name"],
                            "", "", "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                
                # Clear all content before writing
                attendance_sheet.clear()
                if rows:
                    attendance_sheet.append_rows(rows, value_input_option='RAW')
                
                st.session_state.last_sync_time = datetime.now()
                st.session_state.att_batch_updates = []
                st.session_state.has_pending_updates = False
                return True
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 5))
                    st.warning(f"Request rate limit exceeded, retrying in {retry_after} seconds...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"Update failed: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"Update failed: {str(e)}")
                return False
        
        st.error("Maximum retries reached, synchronization failed")
        return False

    # Apply batch updates to Google Sheets - 修复核心部分
    def apply_batch_updates(max_retries=3):
        if not attendance_sheet or not sheet_handler or not st.session_state.att_batch_updates:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 获取当前表格所有数据用于定位行
                all_data = attendance_sheet.get_all_values()
                if not all_data or all_data[0] != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                    st.warning("Sheet format changed, performing full sync instead")
                    return full_update_sheets()

                # 创建ID到行号的映射 (1-based索引)
                id_to_row = {}
                for row_idx, row in enumerate(all_data[1:], start=2):  # 从第二行开始(索引1)对应表格的行号2
                    if len(row) >= 4:
                        try:
                            member_id = int(row[0]) if row[0] else None
                            meeting_id = int(row[2]) if row[2] else None
                            id_to_row[(member_id, meeting_id)] = row_idx
                        except (ValueError, IndexError):
                            continue

                # 准备批量更新请求
                requests = []
                for update in st.session_state.att_batch_updates:
                    member_id = update["member_id"]
                    meeting_id = update.get("meeting_id")
                    update_type = update["type"]
                    new_value = update["value"]

                    if update_type == "attendance":
                        # 查找对应的行
                        key = (member_id, meeting_id)
                        if key in id_to_row:
                            row_idx = id_to_row[key]
                            # 添加更新请求
                            requests.append({
                                "range": f"E{row_idx}",  # is_present列
                                "values": [["TRUE" if new_value else "FALSE"]]
                            })
                            requests.append({
                                "range": f"F{row_idx}",  # updated_at列
                                "values": [[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
                            })
                        else:
                            # 如果找不到对应行，添加新行
                            new_row = [
                                str(member_id),
                                next(m["name"] for m in st.session_state.att_members if m["id"] == member_id),
                                str(meeting_id),
                                next(m["name"] for m in st.session_state.att_meetings if m["id"] == meeting_id),
                                "TRUE" if new_value else "FALSE",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            attendance_sheet.append_rows([new_row], value_input_option='RAW')

                    elif update_type == "new_member":
                        # 检查是否已存在
                        member_exists = any((m_id, None) in id_to_row for m_id in [member_id])
                        if not member_exists:
                            new_row = [
                                str(member_id), new_value, "", "", "FALSE",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ]
                            attendance_sheet.append_rows([new_row], value_input_option='RAW')

                    elif update_type == "new_meeting":
                        # 为每个成员添加会议记录
                        for member in st.session_state.att_members:
                            key = (member["id"], meeting_id)
                            if key not in id_to_row:
                                new_row = [
                                    str(member["id"]), member["name"],
                                    str(meeting_id), new_value,
                                    "FALSE", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ]
                                attendance_sheet.append_rows([new_row], value_input_option='RAW')

                    elif update_type == "delete_meeting":
                        # 删除会议相关记录
                        rows_to_delete = [id_to_row[key] for key in id_to_row if key[1] == meeting_id]
                        # 按行号倒序删除，避免索引混乱
                        for row_idx in sorted(rows_to_delete, reverse=True):
                            attendance_sheet.delete_rows(row_idx)

                # 执行批量更新
                if requests:
                    # 分割为100个请求一组(Google API限制)
                    for i in range(0, len(requests), 100):
                        chunk = requests[i:i+100]
                        # 使用正确的批量更新方法
                        body = {"valueInputOption": "RAW", "data": chunk}
                        sheet_handler.service.spreadsheets().values().batchUpdate(
                            spreadsheetId=attendance_sheet.spreadsheet.id,
                            body=body
                        ).execute()

                # 更新同步状态
                st.session_state.last_sync_time = datetime.now()
                st.session_state.att_batch_updates = []
                st.session_state.has_pending_updates = False
                return True

            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 5))
                    st.warning(f"Rate limit exceeded, retrying in {retry_after}s...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"Batch update failed: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"Batch update failed: {str(e)}")
                return False
        
        st.error("Maximum retries reached, synchronization failed")
        return False

    # Sync data from Google Sheets
    def sync_from_sheets(force=False):
        if not attendance_sheet or not sheet_handler:
            return
        
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data:
                if force:
                    st.session_state.att_members = []
                    st.session_state.att_meetings = []
                    st.session_state.att_records = {}
                return
                
            headers = all_data[0] if len(all_data) > 0 else []
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                st.warning("Google Sheet format is incorrect, using local data")
                return

            # Extract meeting data
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if len(row) >= 4 and row[2] and row[3] and row[2] not in meeting_ids:
                    meeting_ids.add(row[2])
                    try:
                        meetings.append({"id": int(row[2]), "name": row[3]})
                    except (ValueError, IndexError):
                        continue
            
            # Extract member data
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if len(row) >= 2 and row[0] and row[1] and row[0] not in member_ids:
                    member_ids.add(row[0])
                    try:
                        members.append({"id": int(row[0]), "name": row[1]})
                    except (ValueError, IndexError):
                        continue
            
            # Extract attendance records
            records = {}
            for row in all_data[1:]:
                if len(row) >= 5 and row[0] and row[2]:
                    try:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        if any(m["id"] == member_id for m in members) and any(mt["id"] == meeting_id for mt in meetings):
                            records[(member_id, meeting_id)] = row[4].lower() == "true"
                    except (ValueError, IndexError):
                        continue
            
            # Update local state
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
            st.session_state.last_sync_time = datetime.now()
                
        except Exception as e:
            st.warning(f"Synchronization failed: {str(e)}")

    # Initial sync
    sync_from_sheets(force=True)

    # Render attendance table
    def render_attendance_table():
        data = []
        members_to_render = st.session_state.att_members if st.session_state.att_members else [{"id": 0, "name": "No members"}]
        
        for member in members_to_render:
            row = {"Member Name": member["name"]}
            if st.session_state.att_meetings:
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
            else:
                row["Status"] = "No meetings created yet"
                row["Attendance Rates"] = "N/A"
            
            data.append(row)
        
        with st.container():
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    render_attendance_table()

    # Add manual sync button
    col_sync, _ = st.columns([1, 5])
    with col_sync:
        if st.button("🔄 Sync Data", key="sync_button"):
            with st.spinner("Synchronizing with Google Sheet..."):
                if st.session_state.has_pending_updates:
                    apply_batch_updates()
                sync_from_sheets(force=True)
                st.success("Successfully synchronized with Google Sheet")
                st.session_state.att_needs_refresh = True

    # Auto-sync pending updates every 30 seconds
    if st.session_state.has_pending_updates and st.session_state.last_sync_time:
        if datetime.now() - st.session_state.last_sync_time > timedelta(seconds=30):
            with st.spinner("Syncing pending updates..."):
                apply_batch_updates()
                sync_from_sheets(force=True)  # 同步后重新获取数据
                st.success("Pending updates synchronized with Google Sheet")
                st.session_state.att_needs_refresh = True

    st.markdown("---")

    # Get user permissions
    is_admin = st.session_state.get('auth_is_admin', False)

    # Only display edit area for admins
    if is_admin:
        st.header("Attendance Management Tools")
        col_left, col_right = st.columns(2)

        # Left column: Member import + Meeting management
        with col_left:
            # 1. Import members
            with st.container(border=True):
                st.subheader("Import Members")
                uploaded_file = st.file_uploader("Upload members.xlsx", type=["xlsx"], key="member_uploader")
                import_btn = st.button("Import Members", key="att_import_members")
                
                if import_btn and uploaded_file:
                    try:
                        df = pd.read_excel(uploaded_file)
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
                                    st.session_state.att_batch_updates.append({
                                        "type": "attendance",
                                        "member_id": new_id,
                                        "meeting_id": meeting["id"],
                                        "value": False
                                    })
                                st.session_state.att_batch_updates.append({
                                    "type": "new_member",
                                    "member_id": new_id,
                                    "value": name
                                })
                                added += 1
                        
                        st.success(f"Added {added} new members (will sync shortly)")
                        st.session_state.has_pending_updates = True
                        st.session_state.att_needs_refresh = True
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")

            # 2. Meeting management
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
                    
                    st.session_state.att_batch_updates.append({
                        "type": "new_meeting",
                        "meeting_id": new_meeting_id,
                        "value": meeting_name
                    })
                    
                    st.success(f"Added meeting: {meeting_name} (will sync shortly)")
                    st.session_state.has_pending_updates = True
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
                        meeting_records = [(m_id, mt_id) for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id == selected_meeting["id"]]
                        for key in meeting_records:
                            del st.session_state.att_records[key]
                        
                        st.session_state.att_batch_updates.append({
                            "type": "delete_meeting",
                            "meeting_id": selected_meeting["id"],
                            "value": None
                        })
                        
                        st.success(f"Deleted meeting: {selected_meeting['name']} (will sync shortly)")
                        st.session_state.has_pending_updates = True
                        st.session_state.att_needs_refresh = True

        # Right column: Update attendance
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
                        st.session_state.att_batch_updates.append({
                            "type": "attendance",
                            "member_id": member["id"],
                            "meeting_id": selected_meeting["id"],
                            "value": True
                        })
                    
                    st.success(f"All present for {selected_meeting['name']} (will sync shortly)")
                    st.session_state.has_pending_updates = True
                    st.session_state.att_needs_refresh = True

            if st.session_state.att_members and st.session_state.att_meetings:
                selected_member = st.selectbox(
                    "Select Member",
                    st.session_state.att_members,
                    format_func=lambda x: x["name"],
                    key="att_update_member"
                )
                
                current_present = st.session_state.att_records.get((selected_member["id"], selected_meeting["id"]), False)
                is_absent = st.checkbox("Absent", value=not current_present, key="att_is_absent")
                
                if st.button("Save Attendance", key="att_save_attendance"):
                    new_status = not is_absent
                    st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = new_status
                    
                    st.session_state.att_batch_updates.append({
                        "type": "attendance",
                        "member_id": selected_member["id"],
                        "meeting_id": selected_meeting["id"],
                        "value": new_status
                    })
                    
                    status = "absent" if is_absent else "present"
                    st.success(f"Updated {selected_member['name']}'s status to {status} (will sync shortly)")
                    st.session_state.has_pending_updates = True
                    st.session_state.att_needs_refresh = True

        if st.session_state.has_pending_updates:
            st.info("There are pending updates that will be synchronized automatically within 30 seconds. You can also click the Sync Data button to sync immediately.")
    else:
        st.info("You have view-only access. Please contact an administrator for changes.")

    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
