import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {(member_id, meeting_id): bool}

    # ---------------------- 上部分：数据表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 紧凑容器（消除内部间距）
    with st.container():
        st.markdown("""
            <style>
                .stCheckbox {margin: 0 !important; padding: 0 !important;}
                .stDataFrame {margin-top: -20px !important;}
            </style>
        """, unsafe_allow_html=True)
        
        if st.session_state.members and st.session_state.meetings:
            # 生成勾选框（用列布局强制紧凑排列）
            cols = st.columns([2] + [1]*len(st.session_state.meetings) + [1])  # 成员列宽2，其他列宽1
            
            # 表头
            cols[0].write("**Member Name**")
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")
            cols[-1].write("**Attendance Rates**")
            
            # 表格内容（逐行渲染，消除行间距）
            for member in st.session_state.members:
                cols[0].write(member["name"])  # 成员名
                
                # 会议勾选框（紧凑排列）
                for i, meeting in enumerate(st.session_state.meetings):
                    with cols[i+1]:
                        checked = st.checkbox(
                            "",
                            value=st.session_state.attendance.get((member["id"], meeting["id"]), False),
                            key=f"c_{member['id']}_{meeting['id']}",
                            label_visibility="collapsed"
                        )
                        st.session_state.attendance[(member["id"], meeting["id"])] = checked
                
                # 考勤率
                attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance.get((member["id"], m["id"]), False))
                rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
                cols[-1].write(rate)

    # 分隔线（无多余间距）
    st.markdown("---", unsafe_allow_html=True)

    # ---------------------- 下部分：管理功能 ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员（紧凑容器）
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

    # 2. 添加会议（紧凑容器）
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Meeting name", placeholder="e.g., Team Sync", key="meeting_input")
        if st.button("Add Meeting", key="add_btn"):
            if not meeting_name.strip():
                st.error("Enter a meeting name!")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("Meeting exists!")
            else:
                st.session_state.meetings.append({"id": len(st.session_state.meetings)+1, "name": meeting_name.strip()})
                st.success(f"Added: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
