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

    # 保持原有样式
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
            [data-testid="column"] {
                padding: 0 !important;
            }
            .element-container {
                margin: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 切换出勤状态的函数
    def toggle_status(member_id, meeting_id):
        current = st.session_state.attendance.get((member_id, meeting_id), False)
        st.session_state.attendance[(member_id, meeting_id)] = not current

    # 保持原有界面结构
    st.header("Meeting Attendance Records")

    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 构建表格数据
            table_data = []
            for member in st.session_state.members:
                row = [member["name"]]
                attended_count = 0
                
                for meeting in st.session_state.meetings:
                    status = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                    row.append("✓" if status else "✗")
                    if status:
                        attended_count += 1
                
                # 计算出勤率
                total = len(st.session_state.meetings)
                rate = f"{(attended_count/total*100):.1f}%" if total > 0 else "N/A"
                row.append(rate)
                table_data.append(row)
            
            # 显示表格
            columns = ["Member Name"] + [m["name"] for m in st.session_state.meetings] + ["Attendance Rates"]
            df = pd.DataFrame(table_data, columns=columns)
            st.dataframe(df, use_container_width=True)

            # 单独的状态修改区域
            st.subheader("Update Attendance")
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_member = st.selectbox("Select Member", [m["name"] for m in st.session_state.members])
            with col2:
                selected_meeting = st.selectbox("Select Meeting", [m["name"] for m in st.session_state.meetings])
            with col3:
                # 获取成员和会议ID
                member_id = next(m["id"] for m in st.session_state.members if m["name"] == selected_member)
                meeting_id = next(m["id"] for m in st.session_state.meetings if m["name"] == selected_meeting)
                current_status = st.session_state.attendance.get((member_id, meeting_id), False)
                
                # 显示切换按钮
                if st.button(f"Set to {'✗' if current_status else '✓'}", key="toggle_btn"):
                    toggle_status(member_id, meeting_id)
                    st.success(f"Updated {selected_member}'s status for {selected_meeting}")
        
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
