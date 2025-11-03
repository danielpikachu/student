import streamlit as st
import pandas as pd

def render_attendance():
    # 强制清空页面缓存
    st.cache_data.clear()
    
    # ---------------------- 上部分：Meeting Attendance Records（仅表格） ----------------------
    st.header("Meeting Attendance Records")
    
    # 初始化会话状态（仅保留必要数据）
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {meeting_id: {member_id: bool}}

    # 渲染考勤表格（上部分核心）
    table_placeholder = st.empty()  # 用占位符固定表格位置
    with table_placeholder.container():
        if st.session_state.members and st.session_state.meetings:
            # 构建表格数据（仅包含成员、会议列、考勤率）
            data = []
            for member in st.session_state.members:
                row = {"Member Name": member["name"]}
                # 会议出勤勾选（仅在表格内显示）
                for meeting in st.session_state.meetings:
                    # 初始化考勤状态
                    if meeting["id"] not in st.session_state.attendance:
                        st.session_state.attendance[meeting["id"]] = {}
                    if member["id"] not in st.session_state.attendance[meeting["id"]]:
                        st.session_state.attendance[meeting["id"]][member["id"]] = False
                    # 勾选框（仅在表格内渲染）
                    row[meeting["name"]] = st.checkbox(
                        "", 
                        value=st.session_state.attendance[meeting["id"]][member["id"]],
                        key=f"att_{meeting['id']}_{member['id']}"
                    )
                    st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
                # 计算实时考勤率
                attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance[m["id"]][member["id"]])
                row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
                data.append(row)
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No attendance data yet. Add members and meetings below.")

    # ---------------------- 下部分：Attendance Management Tools（仅管理功能） ----------------------
    st.header("Attendance Management Tools")
    
    # 1. 导入成员（单独容器，避免干扰表格）
    with st.container(border=True):
        st.subheader("Import Members")
        if st.button("Import from members.xlsx"):
            try:
                df = pd.read_excel("members.xlsx")
                if "Member Name" in df.columns:
                    new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                    added = 0
                    for name in new_members:
                        if not any(m["name"] == name for m in st.session_state.members):
                            st.session_state.members.append({"id": len(st.session_state.members)+1, "name": name})
                            added += 1
                    st.success(f"Imported {added} members!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议（单独容器，避免干扰表格）
    with st.container(border=True):
        st.subheader("Add Meeting")
        with st.form("add_meeting_form"):
            meeting_name = st.text_input("Meeting Name")
            submit = st.form_submit_button("Add Meeting")
            if submit and meeting_name.strip():
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
                # 初始化该会议的考勤记录
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
                st.success(f"Added meeting: {meeting_name}")

if __name__ == "__main__":
    render_attendance()
