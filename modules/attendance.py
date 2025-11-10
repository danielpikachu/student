# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
    """渲染考勤模块界面，初始全量同步，单次操作单独更新"""
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
        st.error(f"Google Sheets initialization failed: {str(e)}")
        return

    # 初始化会话状态
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False
    # 记录行索引映射（避免每次查询都重新获取全表数据）
    if "row_mapping" not in st.session_state:
        st.session_state.row_mapping = {}  # 格式: {(member_id, meeting_id): row_number}

    # 全量同步数据（初始加载时用）
    def full_sync_sheets():
        """全量同步：从Sheet拉取数据并更新本地状态和行映射"""
        if not attendance_sheet:
            return False
        
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data:
                st.session_state.att_members = []
                st.session_state.att_meetings = []
                st.session_state.att_records = {}
                st.session_state.row_mapping = {}
                return True

            # 验证表头
            headers = all_data[0]
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                st.warning("Sheet format incorrect, resetting...")
                attendance_sheet.clear()
                attendance_sheet.append_rows([headers])
                st.session_state.att_members = []
                st.session_state.att_meetings = []
                st.session_state.att_records = {}
                st.session_state.row_mapping = {}
                return True

            # 提取会议数据（去重）
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if len(row) >= 4 and row[2] and row[3] and row[2] not in meeting_ids:
                    meeting_ids.add(row[2])
                    try:
                        meetings.append({"id": int(row[2]), "name": row[3]})
                    except ValueError:
                        continue

            # 提取成员数据（去重）
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if len(row) >= 2 and row[0] and row[1] and row[0] not in member_ids:
                    member_ids.add(row[0])
                    try:
                        members.append({"id": int(row[0]), "name": row[1]})
                    except ValueError:
                        continue

            # 提取考勤记录和行映射
            records = {}
            row_mapping = {}
            for row_idx, row in enumerate(all_data[1:], start=2):  # 表格行号从2开始（1-based）
                if len(row) >= 5 and row[0] and row[2]:
                    try:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        records[(member_id, meeting_id)] = row[4].lower() == "true"
                        row_mapping[(member_id, meeting_id)] = row_idx
                    except (ValueError, IndexError):
                        continue

            # 更新本地状态
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
            st.session_state.row_mapping = row_mapping
            return True

        except Exception as e:
            st.error(f"Full sync failed: {str(e)}")
            return False

    # 单次操作同步（只更新当前操作的内容）
    def sync_single_operation(update_type, **kwargs):
        """
        单次操作同步到Sheet，只更新必要数据
        update_type: 'attendance' / 'new_member' / 'new_meeting' / 'delete_meeting'
        """
        if not attendance_sheet:
            return False

        try:
            if update_type == "attendance":
                # 更新考勤状态（只更新对应行的is_present和updated_at）
                member_id = kwargs["member_id"]
                meeting_id = kwargs["meeting_id"]
                is_present = kwargs["is_present"]
                key = (member_id, meeting_id)

                # 查找行号，不存在则新增行
                if key in st.session_state.row_mapping:
                    row_idx = st.session_state.row_mapping[key]
                    # 更新E列（is_present）和F列（updated_at）
                    attendance_sheet.update(
                        range_name=f"E{row_idx}:F{row_idx}",
                        values=[["TRUE" if is_present else "FALSE", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]],
                        value_input_option="RAW"
                    )
                else:
                    # 新增行
                    member_name = next(m["name"] for m in st.session_state.att_members if m["id"] == member_id)
                    meeting_name = next(m["name"] for m in st.session_state.att_meetings if m["id"] == meeting_id)
                    new_row = [
                        str(member_id), member_name,
                        str(meeting_id), meeting_name,
                        "TRUE" if is_present else "FALSE",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    # 追加行并记录行号
                    result = attendance_sheet.append_rows([new_row], value_input_option="RAW")
                    # 解析新增行的行号（从响应中提取）
                    row_idx = int(result['updates']['updatedRange'].split('!')[1].split(':')[0][1:])
                    st.session_state.row_mapping[key] = row_idx

            elif update_type == "new_member":
                # 新增成员（为每个现有会议创建一行）
                member_id = kwargs["member_id"]
                member_name = kwargs["member_name"]
                for meeting in st.session_state.att_meetings:
                    key = (member_id, meeting["id"])
                    new_row = [
                        str(member_id), member_name,
                        str(meeting["id"]), meeting["name"],
                        "FALSE",  # 默认缺席
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    result = attendance_sheet.append_rows([new_row], value_input_option="RAW")
                    row_idx = int(result['updates']['updatedRange'].split('!')[1].split(':')[0][1:])
                    st.session_state.row_mapping[key] = row_idx

            elif update_type == "new_meeting":
                # 新增会议（为每个现有成员创建一行）
                meeting_id = kwargs["meeting_id"]
                meeting_name = kwargs["meeting_name"]
                for member in st.session_state.att_members:
                    key = (member["id"], meeting_id)
                    new_row = [
                        str(member["id"]), member["name"],
                        str(meeting_id), meeting_name,
                        "FALSE",  # 默认缺席
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    result = attendance_sheet.append_rows([new_row], value_input_option="RAW")
                    row_idx = int(result['updates']['updatedRange'].split('!')[1].split(':')[0][1:])
                    st.session_state.row_mapping[key] = row_idx

            elif update_type == "delete_meeting":
                # 删除会议（删除所有相关行）
                meeting_id = kwargs["meeting_id"]
                # 收集所有相关行号（倒序删除，避免索引错乱）
                rows_to_delete = [
                    row_idx for (mid, mtid), row_idx in st.session_state.row_mapping.items()
                    if mtid == meeting_id
                ]
                for row_idx in sorted(rows_to_delete, reverse=True):
                    attendance_sheet.delete_rows(row_idx)
                # 更新行映射（移除已删除的记录）
                st.session_state.row_mapping = {
                    k: v for k, v in st.session_state.row_mapping.items()
                    if k[1] != meeting_id
                }

            return True

        except HttpError as e:
            if e.resp.status == 429:
                st.warning("Rate limit exceeded, please try again later")
            else:
                st.error(f"Sync failed: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Sync failed: {str(e)}")
            return False

    # 初始全量同步
    if not st.session_state.att_members or not st.session_state.att_meetings:
        with st.spinner("Initial sync with Google Sheet..."):
            full_sync_sheets()

    # 渲染考勤表格
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

    # 手动同步按钮（用于强制刷新）
    if st.button("🔄 Refresh Data", key="refresh_button"):
        with st.spinner("Refreshing from Google Sheet..."):
            full_sync_sheets()
            st.success("Data refreshed")
            st.session_state.att_needs_refresh = True

    st.markdown("---")

    # 获取管理员权限
    is_admin = st.session_state.get('auth_is_admin', False)

    # 管理员操作区域
    if is_admin:
        st.header("Attendance Management Tools")
        col_left, col_right = st.columns(2)

        # 左列：成员导入 + 会议管理
        with col_left:
            # 1. 导入成员
            with st.container(border=True):
                st.subheader("Import Members")
                uploaded_file = st.file_uploader("Upload members.xlsx", type=["xlsx"], key="member_uploader")
                if st.button("Import Members", key="att_import_members") and uploaded_file:
                    try:
                        df = pd.read_excel(uploaded_file)
                        if "Member Name" not in df.columns:
                            st.error("Excel must contain 'Member Name' column!")
                            return
                        
                        new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                        added = 0
                        
                        for name in new_members:
                            if not any(m["name"] == name for m in st.session_state.att_members):
                                new_id = len(st.session_state.att_members) + 1
                                st.session_state.att_members.append({"id": new_id, "name": name})
                                # 为每个现有会议初始化考勤记录
                                for meeting in st.session_state.att_meetings:
                                    st.session_state.att_records[(new_id, meeting["id"])] = False
                                # 同步到Sheet
                                sync_single_operation(
                                    "new_member",
                                    member_id=new_id,
                                    member_name=name
                                )
                                added += 1
                        
                        st.success(f"Added {added} new members")
                        st.session_state.att_needs_refresh = True
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")

            # 2. 会议管理
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
                    
                    # 为每个现有成员初始化考勤记录
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], new_meeting_id)] = False
                    
                    # 同步到Sheet
                    sync_single_operation(
                        "new_meeting",
                        meeting_id=new_meeting_id,
                        meeting_name=meeting_name
                    )
                    
                    st.success(f"Added meeting: {meeting_name}")
                    st.session_state.att_needs_refresh = True

                if st.session_state.att_meetings:
                    selected_meeting = st.selectbox(
                        "Select meeting to delete",
                        st.session_state.att_meetings,
                        format_func=lambda x: x["name"],
                        key="att_del_meeting"
                    )
                    
                    if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                        # 更新本地状态
                        st.session_state.att_meetings = [
                            m for m in st.session_state.att_meetings 
                            if m["id"] != selected_meeting["id"]
                        ]
                        # 删除相关考勤记录
                        meeting_records = [
                            (mid, mtid) for (mid, mtid) in st.session_state.att_records.keys()
                            if mtid == selected_meeting["id"]
                        ]
                        for key in meeting_records:
                            del st.session_state.att_records[key]
                        
                        # 同步到Sheet
                        sync_single_operation(
                            "delete_meeting",
                            meeting_id=selected_meeting["id"]
                        )
                        
                        st.success(f"Deleted meeting: {selected_meeting['name']}")
                        st.session_state.att_needs_refresh = True

        # 右列：更新考勤
        with col_right.container(border=True):
            st.subheader("Update Attendance")
            
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "Select Meeting", 
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_update_meeting"
                )
                
                # 全选出席
                if st.button("Set All Present", key="att_set_all"):
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                        # 同步到Sheet
                        sync_single_operation(
                            "attendance",
                            member_id=member["id"],
                            meeting_id=selected_meeting["id"],
                            is_present=True
                        )
                    
                    st.success(f"All members marked as present for {selected_meeting['name']}")
                    st.session_state.att_needs_refresh = True

            # 单独更新成员状态
            if st.session_state.att_members and st.session_state.att_meetings:
                selected_member = st.selectbox(
                    "Select Member",
                    st.session_state.att_members,
                    format_func=lambda x: x["name"],
                    key="att_update_member"
                )
                
                current_present = st.session_state.att_records.get(
                    (selected_member["id"], selected_meeting["id"]), 
                    False
                )
                is_absent = st.checkbox("Absent", value=not current_present, key="att_is_absent")
                
                if st.button("Save Attendance", key="att_save_attendance"):
                    new_status = not is_absent
                    st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = new_status
                    
                    # 同步到Sheet
                    sync_single_operation(
                        "attendance",
                        member_id=selected_member["id"],
                        meeting_id=selected_meeting["id"],
                        is_present=new_status
                    )
                    
                    status = "absent" if is_absent else "present"
                    st.success(f"Updated {selected_member['name']} to {status}")
                    st.session_state.att_needs_refresh = True

    else:
        st.info("You have view-only access. Please contact an administrator for changes.")

    # 刷新页面确保显示最新状态
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
