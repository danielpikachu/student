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
    # 保持原有样式，新增部分按钮样式
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
            .management-btn {
                margin-right: 8px;
                margin-bottom: 8px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 考勤表格展示区域
    st.header("Meeting Attendance Records")
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        if st.session_state.members and st.session_state.meetings:
            # 构建表格数据
            data = []
            # 存储每个成员的出勤次数（用于计算出勤率）
            attended_counts = []
            
            for member in st.session_state.members:
                row = [member["name"]]
                attended_count = 0  # 记录当前成员出勤次数
                
                # 交叉单元格：显示复选框控件
                for meeting in st.session_state.meetings:
                    key = f"c_{member['id']}_{meeting['id']}"
                    checked = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                    
                    # 复选框布局
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
                        attended_count += 1  # 累加出勤次数
                    row.append("")  # 占位
            
            # 保存出勤次数并计算出勤率
                attended_counts.append(attended_count)
                total_meetings = len(st.session_state.meetings)
                rate = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "N/A"
                row.append(rate)
                data.append(row)
            
            # 显示表格
            columns = ["Member Name"] + [m["name"] for m in st.session_state.meetings] + ["Attendance Rates"]
            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df, use_container_width=True)
        
        elif not st.session_state.members:
            st.write("No members found. Please import or add members first.")
        else:
            st.write("No meetings found. Please add meetings first.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 考勤管理工具区域（按图片需求重构）
    st.header("Attendance Management Tools")
    management_cols = st.columns(2, gap="large")
    
    # 左侧：会议管理（添加/删除会议）
    with management_cols[0]:
        st.subheader("Meeting Management")
        
        # 添加新会议
        with st.container(border=True):
            st.markdown("### Add New Meeting")
            meeting_name = st.text_input("Meeting name", placeholder="e.g., First Semester Meeting", key="new_meeting_input")
            if st.button("Add Meeting", key="add_meeting_btn", help="Add new meeting to the list"):
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
        
        # 删除会议
        with st.container(border=True):
            st.markdown("### Delete Meeting")
            if st.session_state.meetings:
                selected_meeting = st.selectbox(
                    "Select Meeting to Delete",
                    options=[m["name"] for m in st.session_state.meetings],
                    key="delete_meeting_select"
                )
                if st.button("Delete Meeting", key="delete_meeting_btn", help="Remove selected meeting", type="primary"):
                    # 删除会议及关联的考勤记录
                    meeting_to_delete = next(m for m in st.session_state.meetings if m["name"] == selected_meeting)
                    st.session_state.meetings = [m for m in st.session_state.meetings if m["name"] != selected_meeting]
                    # 清理该会议的考勤数据
                    st.session_state.attendance = {
                        (mid, meid): val 
                        for (mid, meid), val in st.session_state.attendance.items() 
                        if meid != meeting_to_delete["id"]
                    }
                    st.success(f"Deleted meeting: {selected_meeting}")
            else:
                st.write("No meetings available to delete.")
    
    # 右侧：成员管理（添加/移除成员）+ 快捷操作（一键标记全员出席）
    with management_cols[1]:
        # 成员管理
        st.subheader("Member Management")
        
        # 添加单个成员
        with st.container(border=True):
            st.markdown("### Add New Member")
            member_name = st.text_input("Member name", placeholder="e.g., Maciej Mirostaw Wiechna", key="new_member_input")
            if st.button("Add Member", key="add_member_btn", help="Add single member to the list"):
                if not member_name.strip():
                    st.error("Please enter a member name!")
                elif any(m["name"] == member_name.strip() for m in st.session_state.members):
                    st.error("This member already exists!")
                else:
                    st.session_state.members.append({
                        "id": len(st.session_state.members) + 1, 
                        "name": member_name.strip()
                    })
                    st.success(f"Added member: {member_name.strip()}")
        
        # 移除成员
        with st.container(border=True):
            st.markdown("### Remove Member")
            if st.session_state.members:
                selected_member = st.selectbox(
                    "Select Member to Remove",
                    options=[m["name"] for m in st.session_state.members],
                    key="remove_member_select"
                )
                if st.button("Remove Member", key="remove_member_btn", help="Remove selected member", type="primary"):
                    # 删除成员及关联的考勤记录
                    member_to_delete = next(m for m in st.session_state.members if m["name"] == selected_member)
                    st.session_state.members = [m for m in st.session_state.members if m["name"] != selected_member]
                    # 清理该成员的考勤数据
                    st.session_state.attendance = {
                        (mid, meid): val 
                        for (mid, meid), val in st.session_state.attendance.items() 
                        if mid != member_to_delete["id"]
                    }
                    st.success(f"Removed member: {selected_member}")
            else:
                st.write("No members available to remove.")
        
        # 快捷操作：一键标记全员出席
        with st.container(border=True):
            st.markdown("### Quick Actions")
            if st.session_state.members and st.session_state.meetings:
                selected_meeting_for_present = st.selectbox(
                    "Select Meeting",
                    options=[m["name"] for m in st.session_state.meetings],
                    key="mark_present_meeting_select"
                )
                if st.button("Mark All Present", key="mark_all_present_btn", help="Mark all members as present for selected meeting"):
                    meeting_id = next(m["id"] for m in st.session_state.meetings if m["name"] == selected_meeting_for_present)
                    # 更新所有成员该会议的考勤状态为True
                    for member in st.session_state.members:
                        st.session_state.attendance[(member["id"], meeting_id)] = True
                    st.success(f"All members marked as present for: {selected_meeting_for_present}")
            else:
                st.write("Need both members and meetings to use this feature.")
    
    # 保留原有Excel导入成员功能
    with st.container():
        st.subheader("Bulk Import Members")
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

if __name__ == "__main__":
    render_attendance()
