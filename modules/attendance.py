import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（仅保留数据，不绑定UI组件）
    if 'members' not in st.session_state:
        st.session_state.members = []  # 成员列表：[{id, name}]
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 会议列表：[{id, name}]
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 考勤数据：{(member_id, meeting_id): bool}

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 显示表格（纯数据展示，无内嵌勾选框）
    if st.session_state.members and st.session_state.meetings:
        # 构建表格数据
        data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 填充会议出勤状态
            for meeting in st.session_state.meetings:
                row[meeting["name"]] = "✓" if st.session_state.attendance.get((member["id"], meeting["id"]), False) else "✗"
            # 计算考勤率
            attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance.get((member["id"], m["id"]), False))
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            data.append(row)
        
        # 显示纯数据表格（无任何交互组件）
        st.dataframe(pd.DataFrame(data), use_container_width=True)

    # ---------------------- 考勤操作区（外置勾选逻辑） ----------------------
    if st.session_state.members and st.session_state.meetings:
        st.subheader("Update Attendance")
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_member = st.selectbox("Select Member", st.session_state.members, format_func=lambda x: x["name"])
        with col2:
            selected_meeting = st.selectbox("Select Meeting", st.session_state.meetings, format_func=lambda x: x["name"])
        with col3:
            is_present = st.checkbox("Present", value=st.session_state.attendance.get((selected_member["id"], selected_meeting["id"]), False))
            if st.button("Save"):
                st.session_state.attendance[(selected_member["id"], selected_meeting["id"])] = is_present
                st.success(f"Updated {selected_member['name']}'s attendance for {selected_meeting['name']}")

    st.markdown("---")

    # ---------------------- 下部分：Attendance Management Tools ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx"):
            try:
                df = pd.read_excel("members.xlsx")
                if "Member Name" in df.columns:
                    new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                    added = 0
                    for name in new_members:
                        if not any(m["name"] == name for m in st.session_state.members):
                            st.session_state.members.append({"id": len(st.session_state.members) + 1, "name": name})
                            added += 1
                    st.success(f"Imported {added} members!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议（一次点击生效）
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Enter meeting name", placeholder="e.g., Team Meeting 1")
        if st.button("Add Meeting"):
            meeting_name = meeting_name.strip()
            if not meeting_name:
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name for m in st.session_state.meetings):
                st.error("Meeting already exists!")
            else:
                st.session_state.meetings.append({"id": len(st.session_state.meetings) + 1, "name": meeting_name})
                st.success(f"Added meeting: {meeting_name}")

if __name__ == "__main__":
    render_attendance()
