import streamlit as st
import pandas as pd
from datetime import datetime

def render_attendance():
    st.header("Meeting Attendance Tracking")
    st.header("Meeting Attendance Records")

    # 初始化会话状态
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 结构：{meeting_id: {member_id: bool}}

    # 1. 数据管理：导入成员Excel
    st.subheader("Data Management")
    if st.button("Import Members from Excel"):
        try:
            df = pd.read_excel("members.xlsx")
            if "Member Name" in df.columns:
                new_members = df["Member Name"].dropna().str.strip().unique().tolist()
                added = 0
                for name in new_members:
                    if name not in [m["name"] for m in st.session_state.members]:
                        st.session_state.members.append({"id": len(st.session_state.members) + 1, "name": name})
                        added += 1
                st.success(f"Imported {added} members!")
            else:
                st.error("Excel must have 'Member Name' column!")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # 2. 添加会议
    st.subheader("Add Meeting")
    with st.form("add_meeting"):
        meeting_name = st.text_input("Meeting Name")
        if st.form_submit_button("Add Meeting") and meeting_name.strip():
            meeting_id = len(st.session_state.meetings) + 1
            st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
            # 仅当有成员时初始化考勤记录
            if st.session_state.members:
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
            st.success(f"Meeting '{meeting_name}' added!")

    # 3. 渲染考勤表格（严格在Meeting Attendance Records下方）
    if st.session_state.members and st.session_state.meetings:
        table_rows = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 处理每个会议的考勤
            for meeting in st.session_state.meetings:
                # 确保考勤记录存在
                if meeting["id"] not in st.session_state.attendance:
                    st.session_state.attendance[meeting["id"]] = {}
                if member["id"] not in st.session_state.attendance[meeting["id"]]:
                    st.session_state.attendance[meeting["id"]][member["id"]] = False
                # 渲染勾选框并绑定状态
                row[meeting["name"]] = st.checkbox(
                    "", 
                    value=st.session_state.attendance[meeting["id"]][member["id"]],
                    key=f"att_{meeting['id']}_{member['id']}"
                )
                st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
            # 计算考勤率
            attended = sum(
                1 for m in st.session_state.meetings 
                if st.session_state.attendance[m["id"]].get(member["id"], False)
            )
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            table_rows.append(row)
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    elif st.session_state.members:
        st.info("Please add meetings to track attendance.")
    elif st.session_state.meetings:
        st.info("Please import members first.")
    else:
        st.info("Please import members and add meetings.")

if __name__ == "__main__":
    render_attendance()
