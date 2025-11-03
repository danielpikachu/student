import streamlit as st
import pandas as pd

def render_attendance():
    # 第一部分：Meeting Attendance Records（考勤表格区域）
    st.header("Meeting Attendance Records")

    # 第二部分：Attendance Management Tools（功能操作区域）
    st.header("Attendance Management Tools")

    # 初始化会话状态
    st.session_state.members = st.session_state.get("members", [])
    st.session_state.meetings = st.session_state.get("meetings", [])
    st.session_state.attendance = st.session_state.get("attendance", {})  # {meeting_id: {member_id: bool}}

    # ---------- 1. 导入成员（Attendance Management Tools内） ----------
    with st.expander("Import Members", expanded=True):
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
                    st.success(f"Imported {added} members from members.xlsx!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # ---------- 2. 添加会议（Attendance Management Tools内） ----------
    with st.expander("Add Meeting", expanded=True):
        with st.form("add_meeting"):
            meeting_name = st.text_input("Meeting Name")
            if st.form_submit_button("Add Meeting") and meeting_name.strip():
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
                # 强制初始化考勤记录（兼容后续成员添加）
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
                st.success(f"Meeting '{meeting_name}' added!")

    # ---------- 3. 考勤表格渲染（Meeting Attendance Records区域） ----------
    if st.session_state.members and st.session_state.meetings:
        table_data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 处理每个会议的考勤勾选
            for meeting in st.session_state.meetings:
                if meeting["id"] not in st.session_state.attendance:
                    st.session_state.attendance[meeting["id"]] = {}
                if member["id"] not in st.session_state.attendance[meeting["id"]]:
                    st.session_state.attendance[meeting["id"]][member["id"]] = False
                # 渲染勾选框并实时绑定状态
                row[meeting["name"]] = st.checkbox(
                    "", 
                    value=st.session_state.attendance[meeting["id"]][member["id"]],
                    key=f"att_{meeting['id']}_{member['id']}"
                )
                st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
            # 计算实时考勤率
            attended = sum(
                1 for m in st.session_state.meetings 
                if st.session_state.attendance[m["id"]].get(member["id"], False)
            )
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            table_data.append(row)
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    elif st.session_state.members:
        st.info("Please add meetings in 'Attendance Management Tools' to track attendance.")
    elif st.session_state.meetings:
        st.info("Please import members in 'Attendance Management Tools' first.")
    else:
        st.info("Please import members and add meetings in 'Attendance Management Tools'.")

if __name__ == "__main__":
    render_attendance()
