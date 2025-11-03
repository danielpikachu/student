import streamlit as st
import pandas as pd
from datetime import datetime
import os

def render_attendance():
    st.header("Attendance Management")
    
    # 初始化会话状态
    if 'attendance_events' not in st.session_state:
        st.session_state.attendance_events = []
    if 'attendance_records' not in st.session_state:
        st.session_state.attendance_records = []
    if 'members' not in st.session_state:
        st.session_state.members = []
    
    # 上传成员列表Excel
    st.subheader("Member List")
    member_file = st.file_uploader("Upload Member List (Excel)", type=["xlsx", "xls"])
    
    if member_file:
        try:
            df = pd.read_excel(member_file)
            st.session_state.members = df.to_dict('records')
            st.success(f"Loaded {len(st.session_state.members)} members successfully!")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error loading member list: {str(e)}")
    
    # 新增考勤事件
    st.subheader("Create New Attendance Event")
    with st.form("new_attendance_event"):
        event_name = st.text_input("Event Name")
        event_date = st.date_input("Event Date", datetime.today())
        event_time = st.time_input("Event Time")
        submit_event = st.form_submit_button("Create Event")
        
        if submit_event and event_name:
            event_id = len(st.session_state.attendance_events) + 1
            new_event = {
                "id": event_id,
                "name": event_name,
                "date": event_date,
                "time": event_time,
                "created_at": datetime.now()
            }
            st.session_state.attendance_events.append(new_event)
            st.success(f"Event '{event_name}' created successfully!")
    
    # 显示现有事件并进行考勤
    if st.session_state.attendance_events:
        st.subheader("Attendance Records")
        selected_event = st.selectbox(
            "Select Event to Take Attendance",
            st.session_state.attendance_events,
            format_func=lambda x: f"{x['name']} - {x['date']} {x['time']}"
        )
        
        if selected_event and st.session_state.members:
            st.write(f"Taking attendance for: {selected_event['name']}")
            
            # 过滤出该事件的现有考勤记录
            event_records = [
                r for r in st.session_state.attendance_records 
                if r['event_id'] == selected_event['id']
            ]
            
            # 显示成员列表并记录考勤
            with st.form(f"attendance_form_{selected_event['id']}"):
                attendance_data = []
                for member in st.session_state.members:
                    # 获取成员姓名（假设Excel中有'name'列，可根据实际调整）
                    member_name = member.get('name', f"Member {member.get('id', member.index)}")
                    
                    # 检查是否已有考勤记录
                    status = "Present"
                    for record in event_records:
                        if record['member_id'] == member.get('id', member_name):
                            status = record['status']
                            break
                    
                    # 选择考勤状态
                    attendance_status = st.radio(
                        f"Status for {member_name}",
                        ["Present", "Absent", "Late"],
                        index=["Present", "Absent", "Late"].index(status),
                        key=f"attendance_{selected_event['id']}_{member.get('id', member_name)}"
                    )
                    
                    attendance_data.append({
                        "member": member,
                        "status": attendance_status
                    })
                
                submit_attendance = st.form_submit_button("Save Attendance")
                
                if submit_attendance:
                    # 先删除该事件的旧记录
                    st.session_state.attendance_records = [
                        r for r in st.session_state.attendance_records 
                        if r['event_id'] != selected_event['id']
                    ]
                    
                    # 添加新记录
                    for data in attendance_data:
                        st.session_state.attendance_records.append({
                            "event_id": selected_event['id'],
                            "event_name": selected_event['name'],
                            "member_id": data['member'].get('id', data['member'].get('name')),
                            "member_name": data['member'].get('name'),
                            "status": data['status'],
                            "recorded_at": datetime.now()
                        })
                    st.success("Attendance saved successfully!")
        
        # 显示考勤统计
        if event_records:
            st.subheader("Attendance Statistics")
            present_count = sum(1 for r in event_records if r['status'] == "Present")
            absent_count = sum(1 for r in event_records if r['status'] == "Absent")
            late_count = sum(1 for r in event_records if r['status'] == "Late")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Present", present_count)
            col2.metric("Absent", absent_count)
            col3.metric("Late", late_count)
            
            # 显示详细记录
            st.subheader("Detailed Records")
            records_df = pd.DataFrame(event_records)
            st.dataframe(records_df[['member_name', 'status', 'recorded_at']])
