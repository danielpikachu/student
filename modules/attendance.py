import streamlit as st
import pandas as pd
from datetime import datetime

def render_attendance():
    st.header("Attendance Management Tools")  # 完全匹配图片标题

    # 初始化会话状态（仅保留必要字段）
    if 'attendance_events' not in st.session_state:
        st.session_state.attendance_events = []  # 会议列表
    if 'attendance_records' not in st.session_state:
        st.session_state.attendance_records = []  # 考勤记录
    if 'members' not in st.session_state:
        st.session_state.members = []  # 成员列表
    if 'next_member_id' not in st.session_state:
        st.session_state.next_member_id = 1  # 成员ID生成器


    # ---------------------- 1. 核心功能区：按图片顺序排列 ----------------------
    # 第一行：添加会议 + 添加成员（图片顶部两个核心操作）
    col1, col2 = st.columns(2)
    
    # 1.1 左列：Add New Meeting（图片"Add New Meeting"）
    with col1:
        st.subheader("Add New Meeting")
        with st.form("new_meeting_form", clear_on_submit=True):
            event_name = st.text_input("Meeting Name")
            event_date = st.date_input("Date", datetime.today())
            event_time = st.time_input("Time")
            if st.form_submit_button("Add Meeting") and event_name.strip():
                new_event = {
                    "id": len(st.session_state.attendance_events) + 1,
                    "name": event_name.strip(),
                    "date": event_date,
                    "time": event_time
                }
                st.session_state.attendance_events.append(new_event)
                st.success(f"Meeting '{event_name}' added!")

    # 1.2 右列：Add New Member（图片"Add New Member"）
    with col2:
        st.subheader("Add New Member")
        with st.form("new_member_form", clear_on_submit=True):
            member_name = st.text_input("Member Name")
            if st.form_submit_button("Add Member") and member_name.strip():
                # 简单去重
                if not any(m["name"] == member_name.strip() for m in st.session_state.members):
                    st.session_state.members.append({
                        "id": st.session_state.next_member_id,
                        "name": member_name.strip()
                    })
                    st.session_state.next_member_id += 1
                    st.success(f"Member '{member_name}' added!")
                else:
                    st.warning(f"Member '{member_name}' already exists!")


    # 第二行：快速操作（图片"Quick Actions"区域）
    st.subheader("Quick Actions")
    col3, col4 = st.columns(2)

    # 2.1 左列：选择会议 + 标记全部在场（图片"Select Meeting" + "Mark All Present"）
    with col3:
        if st.session_state.attendance_events:
            selected_event = st.selectbox(
                "Select Meeting",
                st.session_state.attendance_events,
                format_func=lambda x: f"{x['name']} - {x['date']} {x['time']}"
            )
            # 标记全部在场按钮
            if st.button("Mark All Present") and st.session_state.members:
                event_id = selected_event["id"]
                # 删除该会议旧记录，添加全部在场新记录
                st.session_state.attendance_records = [
                    r for r in st.session_state.attendance_records if r["event_id"] != event_id
                ]
                for member in st.session_state.members:
                    st.session_state.attendance_records.append({
                        "event_id": event_id,
                        "member_id": member["id"],
                        "member_name": member["name"],
                        "status": "Present",
                        "recorded_at": datetime.now()
                    })
                st.success(f"All present for '{selected_event['name']}'!")
        else:
            st.info("No meetings available")

    # 2.2 右列：导入成员（图片"Import Members from Excel"）
    with col4:
        st.subheader("Import Members from Excel")
        member_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
        if member_file:
            try:
                df = pd.read_excel(member_file)
                if "name" in df.columns:
                    # 提取姓名并去重
                    new_names = [name.strip() for name in df["name"].dropna() if name.strip()]
                    added = 0
                    for name in new_names:
                        if not any(m["name"] == name for m in st.session_state.members):
                            st.session_state.members.append({
                                "id": st.session_state.next_member_id,
                                "name": name
                            })
                            st.session_state.next_member_id += 1
                            added += 1
                    st.success(f"Imported {added} new members!")
                else:
                    st.error("Excel must have 'name' column!")
            except Exception as e:
                st.error(f"Import error: {str(e)}")


    # 第三行：数据管理（图片"Data Management"区域）
    st.subheader("Data Management")
    col5, col6, col7 = st.columns(3)

    # 3.1 左列：删除会议（图片"Select Meeting to Delete"）
    with col5:
        st.write("Delete Meeting")
        if st.session_state.attendance_events:
            del_event = st.selectbox(
                "Select Meeting to Delete",
                st.session_state.attendance_events,
                format_func=lambda x: x["name"],
                key="del_meeting"
            )
            if st.button("Delete Meeting", key="del_meeting_btn"):
                event_id = del_event["id"]
                # 删除会议及关联考勤
                st.session_state.attendance_events = [e for e in st.session_state.attendance_events if e["id"] != event_id]
                st.session_state.attendance_records = [r for r in st.session_state.attendance_records if r["event_id"] != event_id]
                st.success(f"Meeting '{del_event['name']}' deleted!")
        else:
            st.info("No meetings to delete")

    # 3.2 中列：移除成员（图片"Select Member to Remove" + 示例成员名）
    with col6:
        st.write("Remove Member")
        if st.session_state.members:
            del_member = st.selectbox(
                "Select Member to Remove",
                st.session_state.members,
                format_func=lambda x: x["name"],
                key="del_member"
            )
            if st.button("Remove Member", key="del_member_btn"):
                st.session_state.members = [m for m in st.session_state.members if m["id"] != del_member["id"]]
                st.success(f"Member '{del_member['name']}' removed!")
        else:
            # 显示图片中的示例成员名（无数据时提示）
            st.info("e.g., Maciej Mirostaw Wiechna")

    # 3.3 右列：重置考勤数据（图片"Reset Attendance Data"）
    with col7:
        st.write("Reset Attendance")
        st.warning("Will delete all attendance records!")
        if st.button("Reset Attendance Data"):
            st.session_state.attendance_records = []
            st.success("Attendance data reset!")


# 执行界面渲染
if __name__ == "__main__":
    render_attendance()
