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

    # 滚动容器和表格样式优化
    st.markdown("""
        <style>
            .scrollable-table-container {
                max-height: 400px;  /* 限制高度以触发滚动 */
                overflow-y: auto;  /* 垂直滚动条 */
                overflow-x: auto;  /* 水平滚动条 */
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .custom-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            .custom-table th, .custom-table td {
                border: 1px solid #999 !important;  /* 清晰的表格线 */
                padding: 8px 12px;
                text-align: left;
                word-wrap: break-word;
                vertical-align: middle;  /* 垂直居中对齐 */
            }
            .custom-table th {
                background-color: #f0f2f0;
                position: sticky;
                top: 0;  /* 表头固定 */
                z-index: 10;
            }
            .scrollable-table-container::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            .scrollable-table-container::-webkit-scrollbar-thumb {
                background-color: #888;
                border-radius: 5px;
            }
            .scrollable-table-container::-webkit-scrollbar-track {
                background-color: #f1f1f1;
            }
            .stCheckbox {
                margin: 0 auto !important;
                display: block;
            }
        </style>
    """, unsafe_allow_html=True)

    # 创建带滚动条的容器
    st.markdown('<div class="scrollable-table-container">', unsafe_allow_html=True)
    
    # 创建表格
    if st.session_state.members and st.session_state.meetings:
        # 计算列数并设置布局（保证对齐）
        col_count = len(st.session_state.meetings) + 2
        cols = st.columns([3] + [1]*(col_count-2) + [2])
        
        # 表头
        with cols[0]:
            st.markdown('<div class="custom-table th">**Member Name**</div>', unsafe_allow_html=True)
        for i, meeting in enumerate(st.session_state.meetings):
            with cols[i+1]:
                st.markdown(f'<div class="custom-table th">**{meeting["name"]}**</div>', unsafe_allow_html=True)
        with cols[-1]:
            st.markdown('<div class="custom-table th">**Attendance Rates**</div>', unsafe_allow_html=True)
        
        # 表格内容（所有成员都显示，通过滚动条查看）
        for member in st.session_state.members:
            with cols[0]:
                st.markdown(f'<div class="custom-table td">{member["name"]}</div>', unsafe_allow_html=True)
            
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
            rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%" if st.session_state.meetings else "0%"
            with cols[-1]:
                st.markdown(f'<div class="custom-table td">{rate}</div>', unsafe_allow_html=True)
    else:
        st.write("Please add members and meetings to display attendance records.")
    
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
