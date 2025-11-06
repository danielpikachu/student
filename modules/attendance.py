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
    """渲染考勤模块界面，删除updated_at列，确保会议列右侧新增"""
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
        st.session_state.att_members = []  # 成员列表: [{"id": 1, "name": "张三"}, ...]
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []  # 会议列表: [{"id": 1, "name": "会议1"}, ...]
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}  # 考勤记录: {(member_id, meeting_id): True/False, ...}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 核心函数：全量更新Google Sheets（按列结构更新，不含updated_at）
    def full_update_sheets(max_retries=3):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 1. 准备表头行（固定列+会议列）
                # 固定列：member_id, member_name, [各会议列...]
                header = ["member_id", "member_name"]
                # 添加所有会议作为列（会议名称为列名）
                for meeting in st.session_state.att_meetings:
                    header.append(meeting["name"])
                
                # 2. 准备数据行
                rows = [header]  # 先添加表头
                for member in st.session_state.att_members:
                    row = [str(member["id"]), member["name"]]  # 成员ID和名称
                    # 添加该成员在各会议中的考勤状态
                    for meeting in st.session_state.att_meetings:
                        is_present = st.session_state.att_records.get((member["id"], meeting["id"]), False)
                        row.append("TRUE" if is_present else "FALSE")
                    rows.append(row)
                
                # 3. 清除现有内容并写入新数据（保证结构完全一致）
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

    # 从Google Sheets同步数据（按列结构解析，不含updated_at）
    def sync_from_sheets(force=False):
        if not attendance_sheet or not sheet_handler:
            return
        
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data or len(all_data) < 2:  # 至少需要表头和一行数据
                if force:
                    st.session_state.att_members = []
                    st.session_state.att_meetings = []
                    st.session_state.att_records = {}
                return
                
            # 解析表头（验证格式并提取会议列）
            header = all_data[0]
            if len(header) < 2 or header[0] != "member_id" or header[1] != "member_name":
                st.warning("Google Sheet格式不正确，已自动校正")
                full_update_sheets()
                return
            
            # 提取会议信息（表头中member_name之后的列都是会议）
            meeting_columns = header[2:]  # 排除前两列（member_id和member_name）
            meetings = []
            for meeting_name in meeting_columns:
                # 检查是否已有该会议（避免重复）
                if not any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                    meetings.append({"id": len(st.session_state.att_meetings) + 1, "name": meeting_name})
            
            # 合并现有会议和新会议（保留ID连续性）
            existing_meeting_names = [m["name"] for m in st.session_state.att_meetings]
            for meeting in meetings:
                if meeting["name"] not in existing_meeting_names:
                    st.session_state.att_meetings.append(meeting)
            
            # 提取成员信息和考勤记录
            members = []
            member_ids = set()
            records = {}
            for row in all_data[1:]:  # 跳过表头行
                if len(row) < 2 or not row[0] or not row[1]:
                    continue  # 跳过无效行
                
                try:
                    member_id = int(row[0])
                    member_name = row[1].strip()
                    
                    # 添加成员（去重）
                    if member_id not in member_ids:
                        members.append({"id": member_id, "name": member_name})
                        member_ids.add(member_id)
                    
                    # 提取该成员在各会议中的考勤状态
                    for col_idx, meeting in enumerate(st.session_state.att_meetings):
                        # 会议列索引 = 2（前两列是member_id和name） + 会议索引
                        if len(row) > 2 + col_idx:
                            is_present = row[2 + col_idx].lower() == "true"
                            records[(member_id, meeting["id"])] = is_present
                except (ValueError, IndexError):
                    continue  # 跳过格式错误的行
            
            # 更新本地状态
            st.session_state.att_members = members
            st.session_state.att_records = records
                
        except Exception as e:
            st.warning(f"同步失败: {str(e)}")

    # 初始同步
    sync_from_sheets(force=True)

    # 渲染考勤表格（与Sheet列结构一致）
    def render_attendance_table():
        if not st.session_state.att_members and not st.session_state.att_meetings:
            st.info("No members or meetings found. Please add data first.")
            return
            
        # 构建表格数据
        data = []
        for member in st.session_state.att_members:
            row = {"Member Name": member["name"]}
            # 添加各会议的考勤状态
            for meeting in st.session_state.att_meetings:
                row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
            # 计算出勤率
            attended_count = sum(1 for m in st.session_state.att_meetings 
                               if st.session_state.att_records.get((member["id"], m["id"]), False))
            total_meetings = len(st.session_state.att_meetings)
            row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
            data.append(row)
        
        # 显示表格
        st.dataframe(pd.DataFrame(data), use_container_width=True)

    # 渲染表格
    render_attendance_table()

    # 手动同步按钮
    col_sync, _ = st.columns([1, 5])
    with col_sync:
        if st.button("🔄 同步数据", key="sync_button"):
            with st.spinner("正在同步..."):
                sync_from_sheets(force=True)
                full_update_sheets()
                st.success("同步完成")
                st.session_state.att_needs_refresh = True

    st.markdown("---")

    # 操作区域
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    # 左侧：成员导入 + 会议管理
    with col_left:
        # 1. 导入成员
        with st.container(border=True):
            st.subheader("Import Members")
            uploaded_file = st.file_uploader("Upload members.xlsx", type=["xlsx"], key="member_uploader")
            if st.button("Import Members", key="att_import_members"):
                if not uploaded_file:
                    st.error("Please upload an Excel file first")
                    return
                    
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
                            # 为现有会议添加默认缺勤记录
                            for meeting in st.session_state.att_meetings:
                                st.session_state.att_records[(new_id, meeting["id"])] = False
                            added += 1
                    
                    st.success(f"Added {added} new members")
                    full_update_sheets()
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")

        # 2. 会议管理
        with st.container(border=True):
            st.subheader("Manage Meetings")
            # 添加会议（核心：新增会议会在Sheet右侧添加新列）
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
                
                # 新增会议ID = 现有会议数量 + 1
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                
                # 为所有成员添加该会议的默认缺勤记录
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"Added meeting: {meeting_name}")
                # 关键：更新Sheet会在右侧新增一列
                full_update_sheets()
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
                    # 移除会议
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    # 移除相关考勤记录
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    st.success(f"Deleted meeting: {selected_meeting['name']}")
                    full_update_sheets()
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
                
                st.success(f"All present for {selected_meeting['name']}")
                full_update_sheets()
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
                full_update_sheets()
                st.session_state.att_needs_refresh = True

    # 刷新页面
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()

if __name__ == "__main__":
    render_attendance()
