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

    # ---------------------- 上部分：带滚动条的表格区域 ----------------------
    st.header("Meeting Attendance Records")

    # 核心：固定尺寸的滚动容器（限制宽高，超出部分滚动）
    st.markdown("""
        <style>
            .table-container {
                width: 100%;
                max-height: 400px;  /* 固定最大高度，超出则垂直滚动 */
                overflow: auto;    /* 自动出现滚动条 */
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .table-row {
                display: flex;
                width: fit-content;  /* 宽度适应内容，超出则水平滚动 */
                min-width: 100%;     /* 至少占满容器宽度 */
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .table-cell {
                padding: 0 12px;
                min-width: 120px;    /* 单元格最小宽度，避免内容挤压 */
            }
            .header-cell {
                font-weight: bold;
                background-color: #f5f5f5;
            }
            .stCheckbox {margin: 0 !important;}
        </style>
    """, unsafe_allow_html=True)

    # 滚动容器
    with st.markdown('<div class="table-container">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 表头行
            header = ['<div class="table-row">']
            header.append(f'<div class="table-cell header-cell">Member Name</div>')
            for meeting in st.session_state.meetings:
                header.append(f'<div class="table-cell header-cell">{meeting["name"]}</div>')
            header.append(f'<div class="table-cell header-cell">Attendance Rates</div>')
            header.append('</div>')
            st.markdown(''.join(header), unsafe_allow_html=True)

            # 内容行（逐行渲染）
            for member in st.session_state.members:
                row_container = st.container()
                with row_container:
                    st.markdown(f'<div class="table-row">', unsafe_allow_html=True)
                    
                    # 成员名列
                    st.markdown(f'<div class="table-cell">{member["name"]}</div>', unsafe_allow_html=True)
                    
                    # 会议勾选框列
                    for meeting in st.session_state.meetings:
                        col = st.columns(1)[0]
                        with col:
                            checked = st.checkbox(
                                "",
                                value=st.session_state.attendance.get((member["id"], meeting["id"]), False),
                                key=f"c_{member['id']}_{meeting['id']}",
                                label_visibility="collapsed"
                            )
                            st.session_state.attendance[(member["id"], meeting["id"])] = checked
                        st.markdown(f'<div class="table-cell"></div>', unsafe_allow_html=True)
                    
                    # 考勤率列
                    attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance.get((member["id"], m["id"]), False))
                    rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
                    st.markdown(f'<div class="table-cell">{rate}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # 关闭滚动容器

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
