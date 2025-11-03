import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化核心状态（确保每次加载都有默认值）
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}
    if 'last_meeting' not in st.session_state:
        st.session_state.last_meeting = ""  # 记录最后添加的会议

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 表格渲染（仅在有数据时显示，严格隔离）
    if st.session_state.members and st.session_state.meetings:
        # 使用唯一key的容器隔离表格组件
        with st.container(key="attendance_table_container"):
            table_data = []
            for member in st.session_state.members:
                row = {"Member Name": member["name"]}
                # 遍历会议时使用稳定的ID生成key
                for meeting in st.session_state.meetings:
                    meeting_id = meeting["id"]
                    # 确保考勤状态存在
                    if meeting_id not in st.session_state.attendance:
                        st.session_state.attendance[meeting_id] = {}
                    if member["id"] not in st.session_state.attendance[meeting_id]:
                        st.session_state.attendance[meeting_id][member["id"]] = False
                    
                    # 勾选框（绝对唯一的key，无任何标签）
                    row[meeting["name"]] = st.checkbox(
                        label="",
                        value=st.session_state.attendance[meeting_id][member["id"]],
                        key=f"att_{meeting_id}_{member['id']}",
                        label_visibility="collapsed"
                    )
                    # 实时更新状态（无延迟）
                    st.session_state.attendance[meeting_id][member["id"]] = row[meeting["name"]]
                
                # 计算考勤率
                attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance[m["id"]][member["id"]])
                row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
                table_data.append(row)
            
            # 显示表格（无多余样式）
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    # 分隔线（清晰区分区域）
    st.markdown("---")

    # ---------------------- 下部分：Attendance Management Tools ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员（独立容器）
    with st.container(key="import_container"):
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

    # 2. 添加会议（彻底解决点击两次问题）
    with st.container(key="meeting_container"):
        st.subheader("Add Meeting")
        # 输入框与状态绑定（实时同步）
        meeting_name = st.text_input(
            "Enter meeting name",
            value=st.session_state.last_meeting,  # 绑定到状态
            placeholder="e.g., Team Meeting 1",
            key="meeting_input"
        )
        
        # 点击按钮直接处理（无延迟）
        if st.button("Add Meeting", key="add_meeting_btn"):
            meeting_name = meeting_name.strip()
            if not meeting_name:
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name for m in st.session_state.meetings):
                st.error("This meeting already exists!")
            else:
                # 直接添加会议并更新状态
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name})
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
                st.session_state.last_meeting = ""  # 清空输入框
                st.success(f"Meeting '{meeting_name}' added!")

if __name__ == "__main__":
    render_attendance()
