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

    # 样式设置
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
            .status-button {
                width: 100%;
                margin: 2px 0;
                padding: 4px;
                border-radius: 4px;
            }
            .present {
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            .absent {
                background-color: #f44336;
                color: white;
                border: none;
            }
            .dataframe-container {
                margin-top: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    # 处理状态更新（关键改进：在渲染前处理所有点击事件）
    for member in st.session_state.members:
        for meeting in st.session_state.meetings:
            key = f"btn_{member['id']}_{meeting['id']}"
            if st.button("Toggle", key=key, visible=False):  # 隐藏的触发按钮
                # 切换状态
                current_state = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                st.session_state.attendance[(member["id"], meeting["id"])] = not current_state

    st.header("Meeting Attendance Records")

    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 创建表格布局
            cols = st.columns([2] + [1]*len(st.session_state.meetings) + [1])
            
            # 表头
            cols[0].write("**Member Name**")
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")
            cols[-1].write("**Attendance Rate**")
            
            # 表格内容
            for member in st.session_state.members:
                row_cols = st.columns([2] + [1]*len(st.session_state.meetings) + [1])
                row_cols[0].write(member["name"])
                
                attended_count = 0
                
                # 为每个会议创建状态按钮
                for i, meeting in enumerate(st.session_state.meetings):
                    status = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                    btn_key = f"btn_{member['id']}_{meeting['id']}"
                    
                    # 根据状态显示不同按钮
                    if status:
                        row_cols[i+1].button(
                            "Present ✓", 
                            key=f"display_{btn_key}",
                            on_click=lambda k=btn_key: st.session_state.update({k: True}),
                            use_container_width=True,
                            type="primary",
                            args=(btn_key,)
                        )
                        attended_count += 1
                    else:
                        row_cols[i+1].button(
                            "Absent ✗", 
                            key=f"display_{btn_key}",
                            on_click=lambda k=btn_key: st.session_state.update({k: True}),
                            use_container_width=True,
                            type="secondary",
                            args=(btn_key,)
                        )
                
                # 计算出勤率
                total = len(st.session_state.meetings)
                rate = f"{(attended_count/total*100):.1f}%" if total > 0 else "N/A"
                row_cols[-1].write(rate)
        
        elif not st.session_state.members:
            st.write("No members found. Please import members first.")
        else:
            st.write("No meetings found. Please add meetings first.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # 管理功能区域
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
