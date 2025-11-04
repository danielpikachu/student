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
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []  # 成员列表：[{id, name}]
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 会议列表：[{id, name}]
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 考勤数据：{(member_id, meeting_id): bool}

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

    # 从Google Sheets同步数据到本地会话状态
    if attendance_sheet and sheet_handler:
        try:
            all_data = attendance_sheet.get_all_values()
            
            # 检查并创建表头
            if not all_data or all_data[0] != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                attendance_sheet.clear()
                attendance_sheet.append_row(["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"])
            else:
                # 提取成员数据
                members = []
                member_ids = set()
                for row in all_data[1:]:
                    if row[0] not in member_ids and row[0] and row[1]:
                        member_ids.add(row[0])
                        members.append({"id": int(row[0]), "name": row[1]})
                if members:
                    st.session_state.members = members

                # 提取会议数据
                meetings = []
                meeting_ids = set()
                for row in all_data[1:]:
                    if row[2] not in meeting_ids and row[2] and row[3]:
                        meeting_ids.add(row[2])
                        meetings.append({"id": int(row[2]), "name": row[3]})
                if meetings:
                    st.session_state.meetings = meetings

                # 提取考勤数据
                attendance_data = {}
                for row in all_data[1:]:
                    if row[0] and row[2]:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        attendance_data[(member_id, meeting_id)] = row[4].lower() == "true"
                if attendance_data:
                    st.session_state.attendance = attendance_data
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 显示表格
    if st.session_state.members and st.session_state.meetings:
        data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            for meeting in st.session_state.meetings:
                row[meeting["name"]] = "✓" if st.session_state.attendance.get((member["id"], meeting["id"]), False) else "✗"
            attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance.get((member["id"], m["id"]), False))
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%" if st.session_state.meetings else "0%"
            data.append(row)
        
        st.dataframe(pd.DataFrame(data), use_container_width=True)

    # ---------------------- 考勤操作区 ----------------------
    if st.session_state.members and st.session_state.meetings:
        st.subheader("Update Attendance")
        col1, col2, col3 = st.columns(3)
        with col1:
            # 为selectbox添加唯一key
            selected_member = st.selectbox(
                "Select Member", 
                st.session_state.members, 
                format_func=lambda x: x["name"],
                key="attendance_select_member"  # 新增：模块前缀
            )
        with col2:
            # 为selectbox添加唯一key
            selected_meeting = st.selectbox(
                "Select Meeting", 
                st.session_state.meetings, 
                format_func=lambda x: x["name"],
                key="attendance_select_meeting"  # 新增：模块前缀
            )
        with col3:
            # 为checkbox添加唯一key
            is_present = st.checkbox(
                "Present", 
                value=st.session_state.attendance.get((selected_member["id"], selected_meeting["id"]), False),
                key="attendance_present_checkbox"  # 新增：模块前缀
            )
            # 为按钮添加唯一key
            if st.button("Save", key="attendance_save_btn"):  # 新增：模块前缀
                # 更新本地状态
                st.session_state.attendance[(selected_member["id"], selected_meeting["id"])] = is_present
                
                # 同步到Google Sheets
                if attendance_sheet and sheet_handler:
                    try:
                        # 删除旧记录
                        all_rows = attendance_sheet.get_all_values()
                        for i, row in enumerate(all_rows[1:], start=2):
                            if row[0] == str(selected_member["id"]) and row[2] == str(selected_meeting["id"]):
                                attendance_sheet.delete_rows(i)
                        
                        # 添加新记录
                        attendance_sheet.append_row([
                            str(selected_member["id"]),
                            selected_member["name"],
                            str(selected_meeting["id"]),
                            selected_meeting["name"],
                            "TRUE" if is_present else "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                    except Exception as e:
                        st.warning(f"同步到Google Sheets失败: {str(e)}")
                
                st.success(f"Updated {selected_member['name']}'s attendance for {selected_meeting['name']}")

    st.markdown("---")

    # ---------------------- 下部分：Attendance Management Tools ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        # 为按钮添加唯一key
        if st.button("Import from members.xlsx", key="attendance_import_members_btn"):  # 新增：模块前缀
            try:
                df = pd.read_excel("members.xlsx")
                if "Member Name" in df.columns:
                    new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                    added = 0
                    for name in new_members:
                        if not any(m["name"] == name for m in st.session_state.members):
                            member_id = len(st.session_state.members) + 1
                            st.session_state.members.append({"id": member_id, "name": name})
                            added += 1
                            
                            # 同步到Google Sheets
                            if attendance_sheet and sheet_handler:
                                for meeting in st.session_state.meetings:
                                    attendance_sheet.append_row([
                                        str(member_id),
                                        name,
                                        str(meeting["id"]),
                                        meeting["name"],
                                        "FALSE",
                                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    ])
                    st.success(f"Imported {added} members!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议
    with st.container():
        st.subheader("Add Meeting")
        # 为文本输入框添加唯一key
        meeting_name = st.text_input(
            "Enter meeting name", 
            placeholder="e.g., Team Meeting 1",
            key="attendance_meeting_name_input"  # 新增：模块前缀
        )
        # 为按钮添加唯一key
        if st.button("Add Meeting", key="attendance_add_meeting_btn"):  # 新增：模块前缀
            meeting_name = meeting_name.strip()
            if not meeting_name:
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name for m in st.session_state.meetings):
                st.error("Meeting already exists!")
            else:
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name})
                
                # 同步到Google Sheets
                if attendance_sheet and sheet_handler:
                    try:
                        for member in st.session_state.members:
                            attendance_sheet.append_row([
                                str(member["id"]),
                                member["name"],
                                str(meeting_id),
                                meeting_name,
                                "FALSE",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                    except Exception as e:
                        st.warning(f"同步到Google Sheets失败: {str(e)}")
                
                st.success(f"Added meeting: {meeting_name}")

if __name__ == "__main__":
    render_attendance()
