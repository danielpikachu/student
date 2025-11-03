import streamlit as st
import pandas as pd

def render_attendance():
    # 页面布局设置
    st.set_page_config(layout="wide")
    
    # ---------------------- 上部分：Meeting Attendance Records ----------------------
    st.header("Meeting Attendance Records")
    
    # 初始化会话状态
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}

    # 表格显示区域（强制显示，即使无数据也会展示提示）
    st.subheader("Attendance Table")  # 明确的表格标题
    if st.session_state.members and st.session_state.meetings:
        # 构建表格数据
        table_data = []
        for member in st.session_state.members:
            row = {"Member Name": member["name"]}
            # 会议出勤勾选
            for meeting in st.session_state.meetings:
                # 确保考勤状态存在
                if meeting["id"] not in st.session_state.attendance:
                    st.session_state.attendance[meeting["id"]] = {}
                if member["id"] not in st.session_state.attendance[meeting["id"]]:
                    st.session_state.attendance[meeting["id"]][member["id"]] = False
                
                # 渲染勾选框（使用紧凑布局）
                row[meeting["name"]] = st.checkbox(
                    label="",
                    value=st.session_state.attendance[meeting["id"]][member["id"]],
                    key=f"att_{meeting['id']}_{member['id']}",
                    help=f"Mark {member['name']} as present in {meeting['name']}"
                )
                # 更新状态
                st.session_state.attendance[meeting["id"]][member["id"]] = row[meeting["name"]]
            
            # 计算考勤率
            attended_meetings = sum(
                1 for meeting in st.session_state.meetings
                if st.session_state.attendance[meeting["id"]][member["id"]]
            )
            attendance_rate = f"{(attended_meetings / len(st.session_state.meetings) * 100):.1f}%"
            row["Attendance Rates"] = attendance_rate
            table_data.append(row)
        
        # 显示表格（强制显示）
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)
    else:
        # 明确提示如何显示表格
        st.info("To display the attendance table: \n1. Import members using the tool below \n2. Add at least one meeting")

    # 分隔线（清晰区分上下两部分）
    st.markdown("---")

    # ---------------------- 下部分：Attendance Management Tools ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="import_btn"):
            try:
                df = pd.read_excel("members.xlsx")
                if "Member Name" in df.columns:
                    # 提取并去重成员
                    new_members = [
                        name.strip() for name in df["Member Name"].dropna().unique()
                        if name.strip() and name.strip() not in [m["name"] for m in st.session_state.members]
                    ]
                    if new_members:
                        for name in new_members:
                            st.session_state.members.append({
                                "id": len(st.session_state.members) + 1,
                                "name": name
                            })
                        st.success(f"Successfully imported {len(new_members)} members!")
                    else:
                        st.info("No new members to import (all already exist)")
                else:
                    st.error("Excel file must contain a 'Member Name' column!")
            except FileNotFoundError:
                st.error("members.xlsx not found in root directory!")
            except Exception as e:
                st.error(f"Import error: {str(e)}")

    # 2. 添加会议
    with st.container():
        st.subheader("Add Meeting")
        with st.form("add_meeting_form"):
            meeting_name = st.text_input("Enter meeting name", placeholder="e.g., Team Meeting 1")
            submit_meeting = st.form_submit_button("Add Meeting")
            
            if submit_meeting:
                if not meeting_name.strip():
                    st.error("Please enter a meeting name!")
                else:
                    # 检查会议是否已存在
                    if any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                        st.error("This meeting already exists!")
                    else:
                        meeting_id = len(st.session_state.meetings) + 1
                        st.session_state.meetings.append({
                            "id": meeting_id,
                            "name": meeting_name.strip()
                        })
                        # 初始化考勤记录
                        st.session_state.attendance[meeting_id] = {
                            m["id"]: False for m in st.session_state.members
                        }
                        st.success(f"Meeting '{meeting_name.strip()}' added successfully!")

if __name__ == "__main__":
    render_attendance()
