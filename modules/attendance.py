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

    # ---------------------- 上部分：带滚动条的表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 滚动容器样式（同时支持水平和垂直滚动，限制最大10行高度）
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 400px;  /* 调整高度以适应约10行内容 */
                overflow-y: auto;  /* 垂直滚动 */
                overflow-x: auto;  /* 水平滚动 */
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            .scrollable-table::-webkit-scrollbar {
                width: 8px;  /* 垂直滚动条宽度 */
                height: 8px; /* 水平滚动条高度 */
            }
            .scrollable-table::-webkit-scrollbar-thumb {
                background: #ccc;
                border-radius: 4px;
            }
            .stCheckbox {margin: 0 !important; padding: 0 !important;}
            .scrollable-table table {
                border-collapse: collapse;
                width: 100%;
                table-layout: fixed; /* 强制列宽均匀分配，解决对齐问题 */
            }
            .scrollable-table th,
            .scrollable-table td {
                border: 1px solid #999 !important; /* 更清晰的边框线条 */
                padding: 10px 12px;
                text-align: left; /* 统一左对齐 */
                word-wrap: break-word; /* 内容过长时自动换行 */
                height: 40px; /* 固定行高，确保10行高度一致 */
            }
            .scrollable-table th {
                background-color: #f0f2f6; /* 表头背景色，增强区分度 */
                font-weight: bold;
            }
            /* 解决可能的样式覆盖问题 */
            .scrollable-table * {
                box-sizing: border-box;
            }
        </style>
    """, unsafe_allow_html=True)

    # 带滚动条的表格容器
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 计算列数并设置布局（成员列 + 会议列 + 考勤率列）
            col_count = len(st.session_state.meetings) + 2
            cols = st.columns([3] + [1]*(col_count-2) + [2])  # 比例优化
            
            # 表头
            cols[0].write("**Member Name**")
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")
            cols[-1].write("**Attendance Rates**")
            
            # 表格内容（最多显示10行）
            members_to_display = st.session_state.members[:10]  # 只取前10个成员
            for member in members_to_display:
                cols[0].write(member["name"])
                
                # 会议勾选框
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

    st.markdown('</div>', unsafe_allow_html=True)  # 关闭滚动容器

    # 显示记录总数（如果超过10行）
    if len(st.session_state.members) > 10:
        st.caption(f"Showing first 10 members of {len(st.session_state.members)} total")

    # 分隔线
    st.markdown("---")

    # ---------------------- 下部分：管理功能 ----------------------
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

    # 2. 添加会议
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
