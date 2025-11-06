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
    """渲染考勤模块界面（att_前缀命名空间）"""
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
    # 从Google Sheets同步数据到本地会话状态（使用att_前缀状态）
    if attendance_sheet and sheet_handler:
        try:
            all_data = attendance_sheet.get_all_values()
            
            # 检查并创建表头
            expected_headers = ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]
            if not all_data or all_data[0] != expected_headers:
                attendance_sheet.clear()
                attendance_sheet.append_row(expected_headers)
            else:
                # 提取成员数据（更新att_members状态，保持原有次序）
                members = []
                member_ids = set()
                for row in all_data[1:]:
                    if row[0] not in member_ids and row[0] and row[1]:
                        member_ids.add(row[0])
                        members.append({"id": int(row[0]), "name": row[1]})
                if members:
                    st.session_state.att_members = members
                else:
                    st.session_state.att_members = []
                # 提取会议数据（更新att_meetings状态）
                meetings = []
                meeting_ids = set()
                for row in all_data[1:]:
                    if row[2] not in meeting_ids and row[2] and row[3]:
                        meeting_ids.add(row[2])
                        meetings.append({"id": int(row[2]), "name": row[3]})
                if meetings:
                    st.session_state.att_meetings = meetings
                else:
                    st.session_state.att_meetings = []
                # 提取考勤数据（更新att_records状态）
                attendance_data = {}
                for row in all_data[1:]:
                    if row[0] and row[2]:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        attendance_data[(member_id, meeting_id)] = row[4].lower() == "true"
                st.session_state.att_records = attendance_data if attendance_data else {}
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")
    # 初始化会话状态（若未存在）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    # ---------------------- 考勤表格展示 ----------------------
    if st.session_state.att_members and st.session_state.att_meetings:
        data = []
        for member in st.session_state.att_members:
            row = {"Member Name": member["name"]}
            # 填充各会议考勤状态
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
    st.markdown("---")
    # ---------------------- 考勤管理工具 ----------------------
    st.header("Attendance Management Tools")
    # 行布局：Add Meeting（左）+ Update Attendance（右）
    col_add, col_update = st.columns(2)
    
    # 1. 添加会议（左侧）
    with col_add:
        with st.container(border=True):
            st.subheader("Add Meeting")
            meeting_name = st.text_input(
                "Enter meeting name", 
                placeholder="e.g., Team Meeting 1",
                key="att_input_meeting_name"  # 层级化Key：att_模块_输入组件_会议名
            )
            
            if st.button("Add Meeting", key="att_btn_add_meeting"):  # 层级化Key：att_模块_按钮_添加会议
                meeting_name = meeting_name.strip()
                if not meeting_name:
                    st.error("Please enter a meeting name!")
                    return
                
                # 检查是否已存在
                if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                    st.error("Meeting already exists!")
                    return
                
                # 生成新会议ID（自增）
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                
                # 同步到Google Sheets（为每个现有成员创建默认缺勤记录）
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
                        st.success(f"Added meeting: {meeting_name}")
                    except Exception as e:
                        st.warning(f"同步到Google Sheets失败: {str(e)}")
    
    # 2. 更新考勤（右侧）
    with col_update:
        with st.container(border=True):
            st.subheader("Update Attendance")
            if st.session_state.att_members and st.session_state.att_meetings:
                # 选择会议
                selected_meeting = st.selectbox(
                    "Select Meeting", 
                    st.session_state.att_meetings, 
                    format_func=lambda x: x["name"],
                    key="att_select_meeting_update"
                )
                
                # 全员设为出勤按钮
                if st.button("Set All Present", key="att_btn_set_all_present"):
                    # 更新本地状态
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                    st.success(f"All members set to present for {selected_meeting['name']}")
                
                st.markdown("---")
                st.caption("Modify individual attendance status (keep original order):")
                
                # 显示成员列表（带序列号，保持原有次序）
                modified_members = []
                for idx, member in enumerate(st.session_state.att_members, start=1):
                    # 获取当前状态
                    current_status = st.session_state.att_records.get((member["id"], selected_meeting["id"]), False)
                    # 复选框（显示序列号+姓名）
                    is_present = st.checkbox(
                        f"{idx}. {member['name']}",
                        value=current_status,
                        key=f"att_check_member_{member['id']}_{selected_meeting['id']}"
                    )
                    # 记录修改的成员
                    if is_present != current_status:
                        modified_members.append((member, is_present))
                
                # 保存修改按钮
                if st.button("Save Modifications", key="att_btn_save_modifications"):
                    if modified_members:
                        # 更新本地状态并同步到Google Sheets
                        for member, is_present in modified_members:
                            member_id = member["id"]
                            meeting_id = selected_meeting["id"]
                            # 更新本地状态
                            st.session_state.att_records[(member_id, meeting_id)] = is_present
                            
                            # 同步到Google Sheets
                            if attendance_sheet and sheet_handler:
                                try:
                                    # 删除旧记录
                                    all_rows = attendance_sheet.get_all_values()
                                    for i, row in enumerate(all_rows[1:], start=2):
                                        if row[0] == str(member_id) and row[2] == str(meeting_id):
                                            attendance_sheet.delete_rows(i)
                                    # 添加新记录
                                    attendance_sheet.append_row([
                                        str(member_id),
                                        member["name"],
                                        str(meeting_id),
                                        selected_meeting["name"],
                                        "TRUE" if is_present else "FALSE",
                                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    ])
                                except Exception as e:
                                    st.warning(f"同步成员 {member['name']} 失败: {str(e)}")
                        st.success(f"Modified attendance for {len(modified_members)} members!")
                    else:
                        st.info("No modifications made.")
            else:
                st.info("No members or meetings available to update.")
    
    # 3. 导入成员（单独区域）
    with st.container(border=True):
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="att_btn_import_members"):  # 层级化Key：att_模块_按钮_导入成员
            try:
                df = pd.read_excel("members.xlsx")
                if "Member Name" not in df.columns:
                    st.error("Excel must have 'Member Name' column!")
                    return
                
                # 去重并提取有效成员名
                new_member_names = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                added_count = 0
                
                for name in new_member_names:
                    # 检查是否已存在
                    if not any(m["name"] == name for m in st.session_state.att_members):
                        # 生成新成员ID（自增）
                        new_member_id = len(st.session_state.att_members) + 1
                        st.session_state.att_members.append({"id": new_member_id, "name": name})
                        added_count += 1
                        
                        # 同步到Google Sheets（为每个现有会议创建默认缺勤记录）
                        if attendance_sheet and sheet_handler:
                            for meeting in st.session_state.att_meetings:
                                attendance_sheet.append_row([
                                    str(new_member_id),
                                    name,
                                    str(meeting["id"]),
                                    meeting["name"],
                                    "FALSE",  # 默认缺勤
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ])
                
                st.success(f"Imported {added_count} new members!")
            except Exception as e:
                st.error(f"Import failed: {str(e)}")
