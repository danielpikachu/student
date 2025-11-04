import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []  # 存储成员信息，包含id和name
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 存储会议信息，包含id和name
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {(member_id, meeting_id): bool} 存储考勤状态

    # 保持原有样式，增加表格布局优化
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 240px;
                overflow-y: auto;
                overflow-x: auto;
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            .scrollable-table::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            .scrollable-table::-webkit-scrollbar-thumb {
                background: #ccc;
                border-radius: 4px;
            }
            .table-row {
                display: flex;
                border-bottom: 1px solid #ddd;
            }
            .table-header {
                font-weight: bold;
                background-color: #f5f5f5;
            }
            .table-cell {
                flex: 1;
                padding: 8px 12px;
                border-right: 1px solid #ddd;
                min-width: 100px;
            }
            .table-cell:last-child {
                border-right: none;
            }
            .checkbox-center {
                display: flex;
                justify-content: center;
            }
        </style>
    """, unsafe_allow_html=True)

    # 保持原有界面结构
    st.header("Meeting Attendance Records")

    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 表格头部
            header = st.container()
            with header:
                cols = st.columns(len(st.session_state.meetings) + 2)
                with cols[0]:
                    st.markdown('<div class="table-cell table-header">Member Name</div>', unsafe_allow_html=True)
                for i, meeting in enumerate(st.session_state.meetings):
                    with cols[i+1]:
                        st.markdown(f'<div class="table-cell table-header">{meeting["name"]}</div>', unsafe_allow_html=True)
                with cols[-1]:
                    st.markdown('<div class="table-cell table-header">Attendance Rates</div>', unsafe_allow_html=True)

            # 表格内容（逐行生成，确保复选框可交互）
            for member in st.session_state.members:
                row = st.container()
                with row:
                    cols = st.columns(len(st.session_state.meetings) + 2)
                    attended_count = 0

                    # 成员姓名
                    with cols[0]:
                        st.markdown(f'<div class="table-cell">{member["name"]}</div>', unsafe_allow_html=True)

                    # 交叉单元格：可交互的复选框
                    for i, meeting in enumerate(st.session_state.meetings):
                        key = f"cb_{member['id']}_{meeting['id']}"
                        current_state = st.session_state.attendance.get((member['id'], meeting['id']), False)
                        
                        with cols[i+1]:
                            st.markdown('<div class="table-cell checkbox-center">', unsafe_allow_html=True)
                            new_state = st.checkbox(
                                label="",
                                value=current_state,
                                key=key,
                                label_visibility="collapsed"
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 更新出勤状态
                            st.session_state.attendance[(member['id'], meeting['id'])] = new_state
                            if new_state:
                                attended_count += 1

                    # 出勤率计算
                    total_meetings = len(st.session_state.meetings)
                    rate = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "N/A"
                    with cols[-1]:
                        st.markdown(f'<div class="table-cell">{rate}</div>', unsafe_allow_html=True)

        elif not st.session_state.members:
            st.write("No members found. Please import members first.")
        else:
            st.write("No meetings found. Please add meetings first.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 保持原有管理功能区域不变
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="import_btn"):
            try:
                df = pd.read_excel("members.xlsx")
                first_col = df.columns[0]
                new_members = [str(name).strip() for name in df[first_col].dropna().unique() if str(name).strip()]
                added = 0
                for name in new_members:
                    if name not in [m["name"] for m in st.session_state.members]:
                        st.session_state.members.append({
                            "id": len(st.session_state.members) + 1, 
                            "name": name
                        })
                        added += 1
                st.success(f"Imported {added} members from {first_col} column!")
            except FileNotFoundError:
                st.error("File 'members.xlsx' not found!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Meeting name", placeholder="e.g., Team Sync", key="meeting_input")
        if st.button("Add Meeting", key="add_btn"):
            if not meeting_name.strip():
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("This meeting already exists!")
            else:
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1, 
                    "name": meeting_name.strip()
                })
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
