import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 强制初始化会话状态
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}
    if 'temp_meeting_name' not in st.session_state:
        st.session_state.temp_meeting_name = ""

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 仅在成员和会议都存在时渲染表格
    if st.session_state.members and st.session_state.meetings:
        table_data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            for meeting in st.session_state.meetings:
                # 初始化考勤状态
                if meeting["id"] not in st.session_state.attendance:
                    st.session_state.attendance[meeting["id"]] = {}
                if member["id"] not in st.session_state.attendance[meeting["id"]]:
                    st.session_state.attendance[meeting["id"]][member["id"]] = False
                
                # 渲染勾选框（无任何冗余元素）
                row[meeting["name"]] = st.checkbox(
                    "",
                    value=st.session_state.attendance[meeting["id"]][member["id"]],
                    key=f"att_{meeting['id']}_{member['id']}",
                    label_visibility="collapsed"
                )
                st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
            
            # 计算考勤率
            attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance[m["id"]][member["id"]])
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            table_data.append(row)
        
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    st.markdown("---")  # 分隔线

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
                        if name not in [m["name"] for m in st.session_state.members]:
                            st.session_state.members.append({"id": len(st.session_state.members)+1, "name": name})
                            added += 1
                    st.success(f"Imported {added} members!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议（彻底解决多余方框问题）
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input(
            "Enter meeting name",
            placeholder="e.g., Team Meeting 1",
            key="meeting_name_input"
        )
        if st.button("Add Meeting", key="add_meeting_btn"):
            if not meeting_name.strip():
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("This meeting already exists!")
            else:
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
                st.success(f"Meeting '{meeting_name.strip()}' added!")

if __name__ == "__main__":
    render_attendance()
