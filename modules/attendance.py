import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（仅存储数据，不存储UI状态）
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance_data' not in st.session_state:
        st.session_state.attendance_data = {}  # {meeting_id: {member_id: bool}}

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 1. 处理考勤数据更新（纯数据操作，无UI渲染）
    if st.session_state.members and st.session_state.meetings:
        # 初始化新会议的考勤数据
        for meeting in st.session_state.meetings:
            if meeting["id"] not in st.session_state.attendance_data:
                st.session_state.attendance_data[meeting["id"]] = {}
            for member in st.session_state.members:
                if member["id"] not in st.session_state.attendance_data[meeting["id"]]:
                    st.session_state.attendance_data[meeting["id"]][member["id"]] = False

        # 2. 统一渲染表格（一次性生成所有组件）
        table_data = []
        cols = st.columns(len(st.session_state.meetings) + 2)  # 会议列 + 成员列 + 考勤率列
        
        # 表头
        cols[0].write("**Member Name**")
        for i, meeting in enumerate(st.session_state.meetings):
            cols[i+1].write(f"**{meeting['name']}**")
        cols[-1].write("**Attendance Rates**")
        
        # 表内容
        for member in st.session_state.members:
            row = [member["name"]]
            # 考勤勾选框（按列渲染，避免冗余）
            for i, meeting in enumerate(st.session_state.meetings):
                with cols[i+1]:
                    # 唯一key确保不重复渲染
                    checked = st.checkbox(
                        "",
                        value=st.session_state.attendance_data[meeting["id"]][member["id"]],
                        key=f"m{member['id']}_mt{meeting['id']}",
                        label_visibility="collapsed"
                    )
                    st.session_state.attendance_data[meeting["id"]][member["id"]] = checked
                    row.append("✓" if checked else "✗")
            
            # 计算考勤率
            attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance_data[m["id"]][member["id"]])
            rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            row.append(rate)
            table_data.append(row)
        
        # 显示数据表格（纯展示，无交互组件）
        df = pd.DataFrame(
            table_data,
            columns=["Member Name"] + [m["name"] for m in st.session_state.meetings] + ["Attendance Rates"]
        )
        st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # ---------------------- 下部分：Attendance Management Tools ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="import_btn"):
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
        meeting_name = st.text_input("Enter meeting name", placeholder="e.g., Team Meeting 1", key="meeting_name")
        if st.button("Add Meeting", key="add_meeting_btn"):
            meeting_name = meeting_name.strip()
            if not meeting_name:
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name for m in st.session_state.meetings):
                st.error("Meeting already exists!")
            else:
                # 直接添加会议（仅数据操作）
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1,
                    "name": meeting_name
                })
                st.success(f"Meeting '{meeting_name}' added!")

if __name__ == "__main__":
    render_attendance()
