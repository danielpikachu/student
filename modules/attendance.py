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
        
        # 尝试获取工作表，如果不存在则创建
        try:
            attendance_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Attendance"
            )
        except Exception as e:
            st.info(f"Attendance工作表不存在，正在创建...")
            attendance_sheet = sheet_handler.create_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Attendance",
                rows=100,  # 初始行数
                cols=20    # 初始列数
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

    # 确保Google Sheet表头与界面一致
    def ensure_sheet_structure():
        if not attendance_sheet or not sheet_handler:
            return
            
        # 界面表格的列名（成员名 + 会议名 + 出勤率）
        interface_columns = ["Member Name"] + [m["name"] for m in st.session_state.att_meetings] + ["Attendance Rates"]
        
        try:
            # 获取当前Sheet表头
            current_headers = attendance_sheet.row_values(1)
            
            # 如果表头不一致，重新创建表头
            if current_headers != interface_columns:
                # 清空现有内容
                attendance_sheet.clear()
                # 写入新表头（与界面完全一致）
                attendance_sheet.append_row(interface_columns)
                # 设置表头格式（加粗）
                attendance_sheet.format("1:1", {"textFormat": {"bold": True}})
        except Exception as e:
            st.warning(f"设置表格结构失败: {str(e)}")

    # 批量更新Google Sheet数据（与界面表格完全一致）
    def sync_interface_to_sheet():
        if not attendance_sheet or not sheet_handler:
            return
            
        # 确保表头一致
        ensure_sheet_structure()
        
        try:
            # 1. 准备与界面完全相同的数据
            sheet_data = []
            for member in st.session_state.att_members:
                row = [member["name"]]  # 成员名
                # 各会议出勤状态（与界面显示一致：✓/✗）
                for meeting in st.session_state.att_meetings:
                    row.append("✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗")
                # 出勤率（与界面显示一致：百分比）
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row.append(f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%")
                sheet_data.append(row)
            
            # 2. 清除工作表中所有现有数据（包括格式）
            attendance_sheet.clear()
            
            # 3. 重新写入表头
            interface_columns = ["Member Name"] + [m["name"] for m in st.session_state.att_meetings] + ["Attendance Rates"]
            attendance_sheet.append_row(interface_columns)
            attendance_sheet.format("1:1", {"textFormat": {"bold": True}})
            
            # 4. 写入所有数据行
            if sheet_data:
                attendance_sheet.append_rows(sheet_data)
                
                # 5. 设置出勤率列格式为百分比
                if st.session_state.att_meetings:
                    rate_col = len(st.session_state.att_meetings) + 2  # 出勤率列索引
                    attendance_sheet.format(f"{chr(64 + rate_col)}2:{chr(64 + rate_col)}{len(sheet_data) + 1}", 
                                          {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}})
                
                return True
            return False
            
        except HttpError as e:
            if e.resp.status == 429:
                st.warning("同步频率超限，请稍后再试")
            else:
                st.error(f"同步到Google Sheet失败: {str(e)}")
            return False
        except Exception as e:
            st.error(f"同步失败: {str(e)}")
            return False

    # 从Google Sheet同步数据到本地（保持结构一致）
    def sync_sheet_to_interface():
        if not attendance_sheet or not sheet_handler:
            return
            
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data or len(all_data) < 1:
                return
                
            # 表头行（第一行）
            headers = all_data[0]
            if not headers or headers[0] != "Member Name":
                return
                
            # 提取会议名称（从表头第二列到倒数第二列）
            meeting_names = headers[1:-1] if len(headers) > 2 else []
            st.session_state.att_meetings = [
                {"id": i + 1, "name": name} 
                for i, name in enumerate(meeting_names)
            ]
            
            # 提取成员和考勤记录（从第二行开始）
            members = []
            records = {}
            for row_idx, row in enumerate(all_data[1:], start=1):
                if not row or not row[0]:  # 跳过空行或无成员名的行
                    continue
                    
                member_name = row[0].strip()
                member_id = len(members) + 1
                members.append({"id": member_id, "name": member_name})
                
                # 提取各会议出勤状态
                for meeting_idx, meeting in enumerate(st.session_state.att_meetings):
                    # 确保行数据长度足够
                    if meeting_idx + 1 < len(row):
                        status = row[meeting_idx + 1].strip()
                        records[(member_id, meeting["id"])] = (status == "✓")
            
            st.session_state.att_members = members
            st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"从Google Sheet同步失败: {str(e)}")

    # 初始同步（优先从Sheet加载）
    if not st.session_state.att_members or not st.session_state.att_meetings:
        sync_sheet_to_interface()

    # 渲染考勤表格（与Sheet保持一致）
    def render_attendance_table():
        if st.session_state.att_members and st.session_state.att_meetings:
            data = []
            for member in st.session_state.att_members:
                row = {"Member Name": member["name"]}
                # 各会议出勤状态
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                # 出勤率
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                data.append(row)
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            return data
        else:
            st.info("No members or meetings found. Please add data first.")
            return None

    # 渲染表格
    table_data = render_attendance_table()

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
                            # 为现有会议添加默认记录
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                            added += 1
                    
                    st.success(f"Added {added} new members")
                    # 同步到Sheet
                    sync_interface_to_sheet()
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
                
                # 添加到本地状态
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                # 为所有成员添加默认缺勤记录
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                # 同步到Sheet
                sync_interface_to_sheet()
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
                    # 同步到Sheet
                    sync_interface_to_sheet()
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
                # 同步到Sheet
                sync_interface_to_sheet()
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
                # 同步到Sheet
                sync_interface_to_sheet()
                st.session_state.att_needs_refresh = True

    # 刷新界面
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
