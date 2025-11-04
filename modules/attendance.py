import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（保持原有数据结构）
    if 'members' not in st.session_state:
        st.session_state.members = []  # 成员：id + name
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 会议：id + name
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 考勤状态：(member_id, meeting_id) → bool

    # 保持原有样式（未修改）
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 400px;
                overflow-y: auto;
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            .custom-table th, .custom-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            .custom-table th {
                background-color: #f0f2f6;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("Meeting Attendance Records")  # 保持原有标题

    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):  # 保持原有滚动容器
        if st.session_state.members and st.session_state.meetings:
            # 1. 创建表格列结构（与原布局一致）
            # 列定义：成员名列 + 会议列 + 出勤率列
            col_count = 1 + len(st.session_state.meetings) + 1
            cols = st.columns(col_count)

            # 2. 表头（保持原有结构）
            cols[0].write("**Member Name**")  # 成员名列
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")  # 会议列
            cols[-1].write("**Attendance Rate**")  # 出勤率列

            # 3. 表格内容（核心修复：确保复选框在交叉单元格）
            for member in st.session_state.members:
                # 成员名（第一列）
                cols[0].write(member["name"])
                
                attended_count = 0
                # 会议复选框（交叉单元格）
                for i, meeting in enumerate(st.session_state.meetings):
                    # 唯一key确保复选框独立
                    key = f"att_{member['id']}_{meeting['id']}"
                    # 读取当前状态
                    current_val = st.session_state.attendance.get((member['id'], meeting['id']), False)
                    
                    # 在对应会议列显示复选框（核心：严格对应交叉单元格）
                    new_val = cols[i+1].checkbox(
                        label="",
                        value=current_val,
                        key=key,
                        label_visibility="collapsed"
                    )
                    
                    # 更新状态
                    st.session_state.attendance[(member['id'], meeting['id'])] = new_val
                    if new_val:
                        attended_count += 1
                
                # 出勤率（最后一列）
                total = len(st.session_state.meetings)
                rate = f"{(attended_count/total*100):.1f}%" if total > 0 else "N/A"
                cols[-1].write(rate)

        elif not st.session_state.members:
            st.info("No members found. Please import members first.")  # 保持原有提示
        else:
            st.info("No meetings found. Please add meetings first.")  # 保持原有提示

    st.markdown('</div>', unsafe_allow_html=True)  # 保持原有容器闭合

    st.markdown("---")  # 保持原有分隔线

    # 管理功能区域（完全保持原有布局和逻辑）
    st.header("Attendance Management Tools")  # 保持原有标题

    # 1. 导入成员（与之前完全一致）
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

    # 2. 添加会议（与之前完全一致）
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
