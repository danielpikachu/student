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

# 处理Google API错误（避免未安装库导致的导入错误）
try:
    from googleapiclient.errors import HttpError
except ImportError:
    class HttpError(Exception):
        def __init__(self, resp, content, uri=None):
            self.resp = resp
            self.content = content
            self.uri = uri

def render_attendance():
    """渲染考勤模块界面（修复重复表格问题）"""
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

    # 初始化会话状态
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 批量写入数据到Google Sheets
    def batch_write_to_sheets(rows, max_retries=3):
        if not attendance_sheet or not sheet_handler or not rows:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                attendance_sheet.append_rows(rows, value_input_option='RAW')
                return True
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 5))
                    st.warning(f"请求频率超限，将在 {retry_after} 秒后重试...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"批量写入失败: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"批量写入失败: {str(e)}")
                return False
        
        st.error("达到最大重试次数，同步失败")
        return False

    # 批量删除行
    def batch_delete_rows(row_indices):
        if not attendance_sheet or not row_indices:
            return True
            
        for i in sorted(row_indices, reverse=True):
            try:
                attendance_sheet.delete_rows(i)
                time.sleep(0.5)
            except Exception as e:
                st.warning(f"删除行 {i} 失败: {str(e)}")
                return False
        return True

    # 添加会议
    def add_meeting_directly(meeting_name):
        new_meeting_id = len(st.session_state.att_meetings) + 1
        # 更新本地状态
        st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
        
        # 为每个成员添加默认缺勤记录（本地）
        for member in st.session_state.att_members:
            st.session_state.att_records[(member["id"], new_meeting_id)] = False
        
        # 批量准备数据
        if attendance_sheet and sheet_handler and st.session_state.att_members:
            rows_to_add = []
            for member in st.session_state.att_members:
                rows_to_add.append([
                    str(member["id"]),
                    member["name"],
                    str(new_meeting_id),
                    meeting_name,
                    "FALSE",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
            
            if not batch_write_to_sheets(rows_to_add):
                st.warning("本地已添加会议，但同步到Google Sheets失败，请稍后重试")
        
        st.session_state.att_needs_refresh = True

    # 从Google Sheets同步数据
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
            
            # 仅在本地状态为空时初始化
            if not st.session_state.att_meetings:
                st.session_state.att_meetings = meetings
            if not st.session_state.att_members:
                st.session_state.att_members = members
            if not st.session_state.att_records:
                st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"后台同步忽略: {str(e)}")

    # 初始同步
    if not st.session_state.att_meetings or not st.session_state.att_members:
        sync_from_sheets()

    # 渲染考勤表格（只渲染一次）
    def render_attendance_table():
        if st.session_state.att_members and st.session_state.att_meetings:
            data = []
            for member in st.session_state.att_members:
                row = {"Member Name": member["name"]}
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                # 计算出勤率
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                data.append(row)
            # 使用同一个容器渲染表格，确保只存在一个
            table_container = st.container()
            with table_container:
                st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No members or meetings found. Please add data first.")

    # 只在页面上方渲染一次表格
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
                    rows_to_add = []
                    
                    for name in new_members:
                        if not any(m["name"] == name for m in st.session_state.att_members):
                            new_id = len(st.session_state.att_members) + 1
                            st.session_state.att_members.append({"id": new_id, "name": name})
                            # 为现有会议添加默认记录（本地）
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                                rows_to_add.append([
                                    str(new_id),
                                    name,
                                    str(meeting["id"]),
                                    meeting["name"],
                                    "FALSE",
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ])
                            added += 1
                    
                    st.success(f"Added {added} new members")
                    if rows_to_add:
                        if not batch_write_to_sheets(rows_to_add):
                            st.warning("部分数据同步失败")
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
                    # 更新本地状态
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    # 批量删除Sheets中的记录
                    if attendance_sheet and sheet_handler:
                        try:
                            all_rows = attendance_sheet.get_all_values()
                            rows_to_delete = []
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[2] == str(selected_meeting["id"]):
                                    rows_to_delete.append(i)
                            
                            if not batch_delete_rows(rows_to_delete):
                                st.warning("部分记录删除失败")
                        except Exception as e:
                            st.warning(f"删除同步失败: {str(e)}")
                    
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
                # 收集需要删除和添加的记录
                rows_to_delete = []
                rows_to_add = []
                
                if attendance_sheet and sheet_handler:
                    all_rows = attendance_sheet.get_all_values()
                    for i, row in enumerate(all_rows[1:], start=2):
                        if row[2] == str(selected_meeting["id"]):
                            rows_to_delete.append(i)
                
                # 更新本地状态
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                    rows_to_add.append([
                        str(member["id"]),
                        member["name"],
                        str(selected_meeting["id"]),
                        selected_meeting["name"],
                        "TRUE",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
                
                # 执行批量操作
                if attendance_sheet and sheet_handler:
                    if rows_to_delete:
                        batch_delete_rows(rows_to_delete)
                    if not batch_write_to_sheets(rows_to_add):
                        st.warning("部分数据同步失败")
                
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
                # 更新本地状态
                st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = is_present
                
                # 同步到Sheets
                if attendance_sheet and sheet_handler:
                    try:
                        # 先删除旧记录
                        all_rows = attendance_sheet.get_all_values()
                        rows_to_delete = []
                        for i, row in enumerate(all_rows[1:], start=2):
                            if row[0] == str(selected_member["id"]) and row[2] == str(selected_meeting["id"]):
                                rows_to_delete.append(i)
                        
                        if rows_to_delete:
                            batch_delete_rows(rows_to_delete)
                        
                        # 再添加新记录
                        batch_write_to_sheets([[
                            str(selected_member["id"]),
                            selected_member["name"],
                            str(selected_meeting["id"]),
                            selected_meeting["name"],
                            "TRUE" if is_present else "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ]])
                    except Exception as e:
                        st.warning(f"Sync warning: {str(e)}")
                
                st.success(f"Updated {selected_member['name']}'s status")
                st.session_state.att_needs_refresh = True

    # 关键修复：使用Streamlit的rerun机制刷新表格，而不是重新渲染
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        # 通过重新运行整个脚本刷新表格，确保只有一个表格存在
        st.experimental_rerun()
