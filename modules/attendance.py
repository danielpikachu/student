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

    st.header("Meeting Attendance Records")

    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 创建表格数据，包含成员名、各会议出勤状态、出勤率
            data = []
            cols = st.columns([1] + [0.5]*len(st.session_state.meetings) + [1])  # 调整列宽比例
            
            # 表头
            with cols[0]:
                st.write("**Member Name**")
            for i, meeting in enumerate(st.session_state.meetings, 1):
                with cols[i]:
                    st.write(f"**{meeting['name']}**")
            with cols[-1]:
                st.write("**Attendance Rate**")

            # 表内容
            for member in st.session_state.members:
                row = [member["name"]]
                attended_count = 0
                
                # 处理每个会议的复选框
                for i, meeting in enumerate(st.session_state.meetings, 1):
                    key = f"att_{member['id']}_{meeting['id']}"
                    current_val = st.session_state.attendance.get((member['id'], meeting['id']), False)
                    
                    with cols[i]:
                        new_val = st.checkbox("", value=current_val, key=key, label_visibility="collapsed")
                    
                    st.session_state.attendance[(member['id'], meeting['id'])] = new_val
                    if new_val:
                        attended_count += 1
                
                # 计算并显示出勤率（最后一列）
                total = len(st.session_state.meetings)
                rate = f"{(attended_count/total*100):.1f}%" if total > 0 else "N/A"
                row.append(rate)
                data.append(row)
                
                # 显示成员行
                with cols[0]:
                    st.write(member["name"])
                with cols[-1]:
                    st.write(rate)

            # 显示汇总表格（可选，用于数据预览）
            st.markdown("### Attendance Summary")
            summary_cols = ["Member Name"] + [m["name"] for m in st.session_state.meetings] + ["Attendance Rate"]
            summary_data = []
            for member in st.session_state.members:
                summary_row = [member["name"]]
                attended = 0
                for meeting in st.session_state.meetings:
                    status = "✓" if st.session_state.attendance.get((member['id'], meeting['id']), False) else "✗"
                    summary_row.append(status)
                    if status == "✓":
                        attended += 1
                total = len(st.session_state.meetings)
                rate = f"{(attended/total*100):.1f}%" if total > 0 else "N/A"
                summary_row.append(rate)
                summary_data.append(summary_row)
            st.dataframe(pd.DataFrame(summary_data, columns=summary_cols), use_container_width=True)
        
        elif not st.session_state.members:
            st.info("No members found. Please import members first.")
        else:
            st.info("No meetings found. Please add meetings first.")

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
