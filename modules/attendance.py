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
    """渲染考勤模块界面，确保Google Sheet与界面完全一致"""
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

    # 核心修复：全量更新Google Sheets（严格匹配界面数据结构）
    def full_update_sheets(max_retries=3):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 准备表头（与界面数据字段完全一致）
                rows = [["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]]
                
                # 遍历所有成员和会议，生成完整考勤记录
                for member in st.session_state.att_members:
                    for meeting in st.session_state.att_meetings:
                        # 严格获取本地状态中的考勤记录，默认False
                        is_present = st.session_state.att_records.get((member["id"], meeting["id"]), False)
                        rows.append([
                            str(member["id"]),
                            member["name"],
                            str(meeting["id"]),
                            meeting["name"],
                            "TRUE" if is_present else "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                
                # 关键步骤：先清除工作表所有内容，再写入新数据（避免残留）
                attendance_sheet.clear()
                if rows:
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

    # 从Google Sheets同步数据（严格还原到本地状态）
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
                st.warning("Google Sheet格式不正确，已自动校正")
                # 强制使用本地结构重建Sheet
                full_update_sheets()
                return

            # 提取会议数据（去重+格式校验）
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if len(row) >= 4 and row[2] and row[3] and row[2] not in meeting_ids:
                    try:
                        meeting_id = int(row[2])
                        meeting_name = row[3].strip()
                        meetings.append({"id": meeting_id, "name": meeting_name})
                        meeting_ids.add(row[2])
                    except (ValueError, IndexError):
                        continue
            
            # 提取成员数据（去重+格式校验）
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if len(row) >= 2 and row[0] and row[1] and row[0] not in member_ids:
                    try:
                        member_id = int(row[0])
                        member_name = row[1].strip()
                        members.append({"id": member_id, "name": member_name})
                        member_ids.add(row[0])
                    except (ValueError, IndexError):
                        continue
            
            # 提取考勤记录（仅保留存在的成员和会议组合）
            records = {}
            for row in all_data[1:]:
                if len(row) >= 5 and row[0] and row[2]:
                    try:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        # 验证成员和会议是否存在
                        member_exists = any(m["id"] == member_id for m in members)
                        meeting_exists = any(mt["id"] == meeting_id for mt in meetings)
                        if member_exists and meeting_exists:
                            records[(member_id, meeting_id)] = row[4].lower() == "true"
                    except (ValueError, IndexError):
                        continue
            
            # 强制覆盖本地状态，确保与Sheet一致
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"同步失败: {str(e)}")

    # 初始强制同步（确保启动时数据一致）
    sync_from_sheets(force=True)

    # 渲染考勤表格（与Sheet数据1:1对应）
    def render_attendance_table():
        data = []
        # 处理无成员情况
        members_to_render = st.session_state.att_members if st.session_state.att_members else [{"id": 0, "name": "No members"}]
        
        for member in members_to_render:
            row = {"Member Name": member["name"]}
            # 处理有会议的情况（严格显示每个会议的考勤状态）
            if st.session_state.att_meetings:
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                
                # 计算出勤率（与Sheet记录严格对应）
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
            else:
                row["Status"] = "No meetings created yet"
                row["Attendance Rates"] = "N/A"
            
            data.append(row)
        
        # 显示表格
        with st.container():
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    # 渲染表格（确保始终执行）
    render_attendance_table()

    # 手动同步按钮（方便用户主动校准）
    col_sync, _ = st.columns([1, 5])
    with col_sync:
        if st.button("🔄 同步数据", key="sync_button"):
            with st.spinner("正在与Google Sheet同步..."):
                sync_from_sheets(force=True)
                full_update_sheets()
                st.success("已与Google Sheet同步完成")
                st.session_state.att_needs_refresh = True

    st.markdown("---")

    # 操作区域布局
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    # 左侧：成员导入 + 会议管理
    with col_left:
        # 1. 成员导入（支持上传文件+本地读取）
        with st.container(border=True):
            st.subheader("Import Members")
            # 支持上传Excel文件
            uploaded_file = st.file_uploader("Upload members.xlsx", type=["xlsx"], key="member_uploader")
            # 保留本地文件导入按钮
            local_import_btn = st.button("Import from local members.xlsx", key="att_import_local_members")
            # 上传文件导入按钮
            upload_import_btn = st.button("Import from uploaded file", key="att_import_uploaded_members")
            
            # 本地文件导入逻辑
            if local_import_btn:
                try:
                    df = pd.read_excel("members.xlsx")
                    process_member_import(df)
                except FileNotFoundError:
                    st.error("Local members.xlsx not found! Please upload a file instead.")
                except Exception as e:
                    st.error(f"Local import failed: {str(e)}")
            
            # 上传文件导入逻辑
            if upload_import_btn and uploaded_file:
                try:
                    df = pd.read_excel(uploaded_file)
                    process_member_import(df)
                except Exception as e:
                    st.error(f"Upload import failed: {str(e)}")

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
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                
                # 为所有成员添加默认缺勤记录
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                # 立即同步到Sheet
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
                    # 立即同步到Sheet
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
            
            # 一键全到（保留）
            if st.button("Set All Present", key="att_set_all"):
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                
                st.success(f"All present for {selected_meeting['name']}")
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
                st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = is_present
                
                st.success(f"Updated {selected_member['name']}'s status")
                if not full_update_sheets():
                    st.warning("数据同步失败，请稍后重试")
                st.session_state.att_needs_refresh = True

    # 刷新页面确保状态同步
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()

# 提取成员导入公共逻辑
def process_member_import(df):
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
    # 立即同步到Sheet
    if not full_update_sheets():
        st.warning("数据同步失败，请稍后重试")
    st.session_state.att_needs_refresh = True

if __name__ == "__main__":
    render_attendance()
