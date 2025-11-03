import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化会话状态（强制刷新）
    for key in ['members', 'meetings', 'attendance', 'new_meeting_added']:
        if key not in st.session_state:
            st.session_state[key] = [] if key != 'attendance' and key != 'new_meeting_added' else {} if key == 'attendance' else False

    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 表格渲染（完全隔离）
    if st.session_state.members and st.session_state.meetings:
        # 使用容器严格隔离表格组件
        with st.container():
            table_data = []
            for member in st.session_state.members:
                row = {"Member Name": member["name"]}
                for meeting in st.session_state.meetings:
                    # 确保考勤状态初始化
                    if meeting["id"] not in st.session_state.attendance:
                        st.session_state.attendance[meeting["id"]] = {}
                    if member["id"] not in st.session_state.attendance[meeting["id"]]:
                        st.session_state.attendance[meeting["id"]][member["id"]] = False
                    
                    # 勾选框（彻底隐藏标签）
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
                        if name not in [m["name"] for m in st.session_state.members]:
                            st.session_state.members.append({"id": len(st.session_state.members)+1, "name": name})
                            added += 1
                    st.success(f"Imported {added} members!")
                else:
                    st.error("Excel must have 'Member Name' column!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议（解决点击两次问题）
    with st.container():
        st.subheader("Add Meeting")
        # 独立状态存储会议名称
        meeting_name = st.text_input(
            "Enter meeting name",
            placeholder="e.g., Team Meeting 1",
            key="meeting_name"
        )
        
        # 点击事件处理（强制刷新状态）
        if st.button("Add Meeting", key="add_meeting"):
            if not meeting_name.strip():
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("Meeting already exists!")
            else:
                # 直接添加会议并强制标记状态更新
                meeting_id = len(st.session_state.meetings) + 1
                st.session_state.meetings.append({"id": meeting_id, "name": meeting_name.strip()})
                st.session_state.attendance[meeting_id] = {m["id"]: False for m in st.session_state.members}
                st.session_state.new_meeting_added = not st.session_state.new_meeting_added  # 状态翻转触发刷新
                st.success(f"Meeting '{meeting_name.strip()}' added!")

    # 强制页面刷新（解决Streamlit状态延迟）
    if st.session_state.new_meeting_added:
        st.experimental_rerun()

if __name__ == "__main__":
    render_attendance()
