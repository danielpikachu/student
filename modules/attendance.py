import streamlit as st
import pandas as pd
from datetime import datetime

def render_attendance():
    st.header("Meeting Attendance Tracking")  # 匹配标题
    st.header("Meeting Attendance Records")   # 匹配子标题

    # 初始化会话状态
    if 'members' not in st.session_state:
        st.session_state.members = []  # 成员列表
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 会议列表
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 考勤记录：{meeting_id: {member_id: bool}}

    # ---------------------- 1. 数据管理：导入成员Excel（指定文件members.xlsx） ----------------------
    st.subheader("Data Management")
    if st.button("Import Members from Excel"):
        try:
            df = pd.read_excel("members.xlsx")
            if "Member Name" in df.columns:
                # 提取成员并去重
                new_members = df["Member Name"].dropna().str.strip().unique().tolist()
                added = 0
                for name in new_members:
                    if name not in [m["name"] for m in st.session_state.members]:
                        st.session_state.members.append({"id": len(st.session_state.members) + 1, "name": name})
                        added += 1
                st.success(f"Imported {added} members from members.xlsx!")
            else:
                st.error("Excel must have 'Member Name' column!")
        except Exception as e:
            st.error(f"Error importing: {str(e)}")

    # ---------------------- 2. 添加会议（用于生成考勤列） ----------------------
    st.subheader("Add Meeting")
    with st.form("add_meeting_form"):
        meeting_name = st.text_input("Meeting Name")
        if st.form_submit_button("Add Meeting") and meeting_name.strip():
            meeting_id = len(st.session_state.meetings) + 1
            st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
            st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
            st.success(f"Meeting '{meeting_name}' added!")

    # ---------------------- 3. 考勤表格：可勾选 + 考勤率实时计算 ----------------------
    if st.session_state.members and st.session_state.meetings:
        # 构建表格数据
        table_data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 考勤列
            for meeting in st.session_state.meetings:
                row[meeting["name"]] = st.checkbox(
                    "", 
                    value=st.session_state.attendance[meeting["id"]].get(member["id"], False),
                    key=f"attendance_{meeting['id']}_{member['id']}"
                )
                # 实时更新考勤记录
                st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
            # 计算考勤率
            attended = sum(1 for m in st.session_state.meetings 
                          if st.session_state.attendance[m["id"]].get(member["id"], False))
            rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%" if st.session_state.meetings else "0%"
            row["Attendance Rates"] = rate
            table_data.append(row)
        
        # 显示表格
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    else:
        st.info("Please import members and add meetings first.")

if __name__ == "__main__":
    render_attendance()
