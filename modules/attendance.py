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

    # ---------------------- 上部分：带滚动条的表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 滚动容器和表格样式（强制显示边框并解决对齐问题）
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
                border-collapse: collapse;  /* 合并边框 */
                table-layout: fixed;  /* 固定布局确保列对齐 */
            }
            .custom-table th, .custom-table td {
                border: 1px solid #ddd !important;  /* 强制显示所有边框 */
                padding: 8px 12px;
                text-align: left;
                vertical-align: middle;  /* 垂直居中对齐 */
                word-wrap: break-word;
            }
            .checkbox-cell {
                text-align: center !important;
            }
            /* 解决Streamlit默认样式冲突 */
            [data-testid="column"] {
                padding: 0 !important;
            }
            .element-container {
                margin: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 带滚动条的表格容器
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        # 只有当有成员时才显示表格
        if st.session_state.members and st.session_state.meetings:
            # 创建数据表格
            data = []
            for member in st.session_state.members:
                row = [member["name"]]
                attended_count = 0
                
                # 为每个会议添加复选框
                for meeting in st.session_state.meetings:
                    key = f"c_{member['id']}_{meeting['id']}"
                    checked = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                    
                    # 使用列布局确保复选框居中
                    cols = st.columns([1])
                    with cols[0]:
                        new_checked = st.checkbox(
                            "",
                            value=checked,
                            key=key,
                            label_visibility="collapsed"
                        )
                        st.session_state.attendance[(member["id"], meeting["id"])] = new_checked
                    
                    if new_checked:
                        attended_count += 1
                    row.append("✓" if new_checked else "✗")  # 显示勾选状态
                
                # 计算考勤率
                total_meetings = len(st.session_state.meetings)
                rate = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "N/A"
                row.append(rate)
                data.append(row)
            
            # 创建DataFrame并显示
            columns = ["Member Name"] + [m["name"] for m in st.session_state.meetings] + ["Attendance Rates"]
            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df, use_container_width=True)
        
        elif not st.session_state.members:
            st.write("No members found. Please import members first.")
        else:
            st.write("No meetings found. Please add meetings first.")

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
                # 取Excel的第一列作为成员名
                first_col = df.columns[0]
                # 提取非空且去重的成员名
                new_members = [str(name).strip() for name in df[first_col].dropna().unique() if str(name).strip()]
                added = 0
                for name in new_members:
                    # 避免重复添加
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
                # 添加新会议
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1, 
                    "name": meeting_name.strip()
                })
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
