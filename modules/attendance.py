import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（仅存储核心数据）
    if 'members' not in st.session_state:
        st.session_state.members = []  # [{id, name}]
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # [{id, name}]
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {(member_id, meeting_id): bool}

    # ---------------------- 上部分：数据表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 表格区域（包含打勾功能，紧凑布局）
    if st.session_state.members and st.session_state.meetings:
        # 构建表格数据（含勾选状态）
        table_data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 为每个会议生成勾选框
            for meeting in st.session_state.meetings:
                # 唯一标识键（避免重复渲染）
                key = f"check_{member['id']}_{meeting['id']}"
                # 渲染勾选框（紧凑模式）
                checked = st.checkbox(
                    label="",  # 无标签
                    value=st.session_state.attendance.get((member["id"], meeting["id"]), False),
                    key=key,
                    label_visibility="collapsed",  # 彻底隐藏标签
                    help=""  # 无帮助提示
                )
                # 实时更新状态
                st.session_state.attendance[(member["id"], meeting["id"])] = checked
                row[meeting["name"]] = "✓" if checked else "✗"  # 表格显示符号
            
            # 计算考勤率
            attended = sum(
                1 for m in st.session_state.meetings 
                if st.session_state.attendance.get((member["id"], m["id"]), False)
            )
            row["Attendance Rates"] = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
            table_data.append(row)
        
        # 显示表格（仅展示数据，勾选框在表格上方独立渲染）
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    else:
        st.info("Add members and meetings below to start tracking attendance")

    # 分隔线（严格区分上下部分）
    st.markdown("---")

    # ---------------------- 下部分：成员导入 + 会议添加 ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container(border=True):
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
    with st.container(border=True):
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Enter meeting name", placeholder="e.g., Q1 Meeting", key="meeting_input")
        if st.button("Add Meeting", key="add_meeting_btn"):
            meeting_name = meeting_name.strip()
            if not meeting_name:
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name for m in st.session_state.meetings):
                st.error("This meeting already exists!")
            else:
                st.session_state.meetings.append({"id": len(st.session_state.meetings) + 1, "name": meeting_name})
                st.success(f"Meeting '{meeting_name}' added!")

if __name__ == "__main__":
    render_attendance()
