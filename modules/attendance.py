import streamlit as st
import pandas as pd
import uuid

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []  # 存储成员信息，包含id和name
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 存储会议信息，包含id、name和uuid
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {(member_id, meeting_uuid): bool} 存储考勤状态

    # ---------------------- 上部分：带滚动条的表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 滚动容器和表格样式
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 400px;
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
            .custom-table {
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }
            .custom-table th, .custom-table td {
                border: 1px solid #ddd !important;
                padding: 8px 12px;
                text-align: left;
                vertical-align: middle;
                word-wrap: break-word;
            }
            .checkbox-cell {
                text-align: center !important;
            }
            /* 解决Streamlit组件间距问题 */
            .stCheckbox {
                display: inline-flex !important;
                margin: 0 auto !important;
            }
            [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
                gap: 0.25rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 带滚动条的表格容器
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members:
            # 创建表格
            cols = st.columns([3] + [1]*len(st.session_state.meetings) + [2])
            
            # 表头
            cols[0].write("**Member Name**")
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")
            cols[-1].write("**Attendance Rates**")
            
            # 分隔表头和内容的水平线
            st.markdown("---", unsafe_allow_html=True)
            
            # 表格内容
            for member in st.session_state.members:
                row_cols = st.columns([3] + [1]*len(st.session_state.meetings) + [2])
                
                # 成员名
                row_cols[0].write(member["name"])
                
                # 会议考勤勾选框
                for i, meeting in enumerate(st.session_state.meetings):
                    # 使用唯一key确保勾选框正确关联
                    key = f"att_{member['id']}_{meeting['uuid']}"
                    
                    # 获取当前考勤状态
                    current_state = st.session_state.attendance.get(
                        (member['id'], meeting['uuid']), False
                    )
                    
                    # 在对应单元格显示勾选框
                    with row_cols[i+1]:
                        new_state = st.checkbox(
                            label="",
                            value=current_state,
                            key=key,
                            label_visibility="collapsed"
                        )
                        # 更新考勤状态
                        st.session_state.attendance[(member['id'], meeting['uuid'])] = new_state
                
                # 计算并显示考勤率
                total_meetings = len(st.session_state.meetings)
                if total_meetings == 0:
                    rate = "N/A"
                else:
                    attended = 0
                    for meeting in st.session_state.meetings:
                        if st.session_state.attendance.get((member['id'], meeting['uuid']), False):
                            attended += 1
                    rate = f"{(attended / total_meetings * 100):.1f}%"
                row_cols[-1].write(rate)
                
                # 行分隔线
                st.markdown("---", unsafe_allow_html=True)
        else:
            st.write("No members found. Please import members first.")

    st.markdown('</div>', unsafe_allow_html=True)

    # 分隔线
    st.markdown("---")

    # ---------------------- 下部分：管理功能 ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members", key="import_btn"):
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
                # 为每个会议生成唯一UUID，确保勾选框key的唯一性
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1, 
                    "name": meeting_name.strip(),
                    "uuid": str(uuid.uuid4())  # 用于生成唯一key
                })
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
