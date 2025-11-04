import streamlit as st
import pandas as pd
import os

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

    # 滚动容器样式
    st.markdown("""
        <style>
            .table-container {
                width: 100%;
                max-height: 400px;
                overflow: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .table-row {display: flex; width: fit-content; min-width: 100%; padding: 8px 0; border-bottom: 1px solid #eee;}
            .table-cell {padding: 0 12px; min-width: 120px;}
            .header-cell {font-weight: bold; background-color: #f5f5f5;}
            .stCheckbox {margin: 0 !important;}
        </style>
    """, unsafe_allow_html=True)

    # 表格渲染
    with st.markdown('<div class="table-container">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 表头
            header = ['<div class="table-row">']
            header.append(f'<div class="table-cell header-cell">Member Name</div>')
            for meeting in st.session_state.meetings:
                header.append(f'<div class="table-cell header-cell">{meeting["name"]}</div>')
            header.append(f'<div class="table-cell header-cell">Attendance Rates</div>')
            header.append('</div>')
            st.markdown(''.join(header), unsafe_allow_html=True)

            # 内容行
            for member in st.session_state.members:
                with st.container():
                    st.markdown(f'<div class="table-row">', unsafe_allow_html=True)
                    st.markdown(f'<div class="table-cell">{member["name"]}</div>', unsafe_allow_html=True)
                    
                    for meeting in st.session_state.meetings:
                        checked = st.checkbox(
                            "",
                            value=st.session_state.attendance.get((member["id"], meeting["id"]), False),
                            key=f"c_{member['id']}_{meeting['id']}",
                            label_visibility="collapsed"
                        )
                        st.session_state.attendance[(member["id"], meeting["id"])] = checked
                        st.markdown(f'<div class="table-cell"></div>', unsafe_allow_html=True)
                    
                    attended = sum(1 for m in st.session_state.meetings if st.session_state.attendance.get((member["id"], m["id"]), False))
                    rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%"
                    st.markdown(f'<div class="table-cell">{rate}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    # ---------------------- 下部分：管理功能 ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员（修复0成员问题）
    with st.container():
        st.subheader("Import Members")
        # 显示当前成员数量（辅助调试）
        st.info(f"Current members in system: {len(st.session_state.members)}")
        
        if st.button("Import from members.xlsx", key="import_btn"):
            # 检查文件是否存在
            if not os.path.exists("members.xlsx"):
                st.error("File not found! 'members.xlsx' does not exist in root directory.")
                return
            
            try:
                df = pd.read_excel("members.xlsx")
                st.success("File loaded successfully!")
                
                # 检查列是否存在
                if "Member Name" not in df.columns:
                    st.error("Excel file must contain a column named 'Member Name' (case-sensitive).")
                    st.write("Columns found in Excel:", df.columns.tolist())
                    return
                
                # 提取并清洗成员数据
                raw_members = df["Member Name"].dropna().tolist()  # 保留所有非空值
                cleaned_members = [str(name).strip() for name in raw_members if str(name).strip()]  # 去除空字符串
                unique_members = list(set(cleaned_members))  # 去重
                
                st.write(f"Found {len(unique_members)} unique members in Excel.")
                
                # 筛选新成员（不在现有列表中）
                existing_names = [m["name"] for m in st.session_state.members]
                new_members = [name for name in unique_members if name not in existing_names]
                
                if new_members:
                    # 添加新成员
                    for name in new_members:
                        st.session_state.members.append({
                            "id": len(st.session_state.members) + 1,
                            "name": name
                        })
                    st.success(f"Successfully imported {len(new_members)} new members!")
                else:
                    st.info("No new members to import. All members from Excel are already in the system.")
                
            except Exception as e:
                st.error(f"Import failed: {str(e)}")

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
                st.session_state.meetings.append({"id": len(st.session_state.meetings)+1, "name": meeting_name.strip()})
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
