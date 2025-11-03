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
    
    # 成员管理区域
    st.subheader("成员管理")
    
    # 手动添加成员
    with st.expander("添加新成员", expanded=False):
        with st.form("add_member_form"):
            col1, col2 = st.columns(2)
            with col1:
                member_name = st.text_input("成员姓名*")
                member_id = st.text_input("成员ID（可选）")
            with col2:
                member_department = st.text_input("部门（可选）")
                member_role = st.text_input("职位（可选）")
            
            submit_member = st.form_submit_button("添加成员")
            
            if submit_member:
                if not member_name:
                    st.error("成员姓名不能为空")
                else:
                    # 生成唯一ID（如果未提供）
                    if not member_id:
                        member_id = f"MEM{len(st.session_state.members) + 1:03d}"
                    
                    new_member = {
                        "id": member_id,
                        "name": member_name,
                        "department": member_department,
                        "role": member_role,
                        "added_at": datetime.now()
                    }
                    
                    # 检查ID是否重复
                    if any(m["id"] == member_id for m in st.session_state.members):
                        st.error(f"成员ID {member_id} 已存在")
                    else:
                        st.session_state.members.append(new_member)
                        st.success(f"成功添加成员：{member_name}")
    
    # 显示当前成员列表
    if st.session_state.members:
        st.subheader("当前成员列表")
        members_df = pd.DataFrame(st.session_state.members)
        # 只显示关键列
        st.dataframe(members_df[["id", "name", "department", "role"]], use_container_width=True)
        
        # 提供下载和更新选项
        col1, col2 = st.columns(2)
        with col1:
            # 下载当前成员列表
            csv = members_df.to_csv(index=False)
            st.download_button(
                "下载成员列表",
                data=csv,
                file_name="members.csv",
                mime="text/csv"
            )
        with col2:
            # 重新上传成员列表（覆盖现有）
            update_file = st.file_uploader("上传新成员列表（覆盖现有）", type=["xlsx", "xls"], key="update_members")
            if update_file:
                try:
                    df = pd.read_excel(update_file)
                    st.session_state.members = df.to_dict('records')
                    st.success(f"已更新成员列表，共 {len(st.session_state.members)} 人")
                except Exception as e:
                    st.error(f"更新失败：{str(e)}")
    else:
        st.info("暂无成员数据，请添加成员或上传成员列表")
    
    # 新增考勤事件（保持不变）
    st.subheader("创建考勤事件")
    with st.form("new_attendance_event"):
        event_name = st.text_input("事件名称*")
        event_date = st.date_input("事件日期", datetime.today())
        event_time = st.time_input("事件时间")
        submit_event = st.form_submit_button("创建事件")
        
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
            st.success(f"事件 '{event_name}' 创建成功！")
        elif submit_event:
            st.error("事件名称不能为空")
    
    # 考勤记录管理（保持不变）
    if st.session_state.attendance_events:
        st.subheader("考勤记录")
        selected_event = st.selectbox(
            "选择事件",
            st.session_state.attendance_events,
            format_func=lambda x: f"{x['name']} - {x['date']} {x['time']}"
        )
        
        if selected_event and st.session_state.members:
            st.write(f"正在记录：{selected_event['name']}")
            
            # 过滤该事件的现有记录
            event_records = [
                r for r in st.session_state.attendance_records 
                if r['event_id'] == selected_event['id']
            ]
            
            # 记录考勤
            with st.form(f"attendance_form_{selected_event['id']}"):
                attendance_data = []
                for member in st.session_state.members:
                    member_name = member["name"]
                    member_id = member["id"]
                    
                    # 检查现有状态
                    status = "Present"
                    for record in event_records:
                        if record['member_id'] == member_id:
                            status = record['status']
                            break
                    
                    attendance_status = st.radio(
                        f"{member_name} ({member_id})",
                        ["Present", "Absent", "Late"],
                        index=["Present", "Absent", "Late"].index(status),
                        key=f"att_{selected_event['id']}_{member_id}"
                    )
                    attendance_data.append({
                        "member": member,
                        "status": attendance_status
                    })
                
                submit_attendance = st.form_submit_button("保存考勤")
                if submit_attendance:
                    # 删除旧记录
                    st.session_state.attendance_records = [
                        r for r in st.session_state.attendance_records 
                        if r['event_id'] != selected_event['id']
                    ]
                    # 添加新记录
                    for data in attendance_data:
                        st.session_state.attendance_records.append({
                            "event_id": selected_event['id'],
                            "event_name": selected_event['name'],
                            "member_id": data['member']['id'],
                            "member_name": data['member']['name'],
                            "status": data['status'],
                            "recorded_at": datetime.now()
                        })
                    st.success("考勤已保存！")
        
        # 显示统计
        if event_records:
            st.subheader("考勤统计")
            present = sum(1 for r in event_records if r['status'] == "Present")
            absent = sum(1 for r in event_records if r['status'] == "Absent")
            late = sum(1 for r in event_records if r['status'] == "Late")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("出席", present)
            col2.metric("缺席", absent)
            col3.metric("迟到", late)
            
            st.subheader("详细记录")
            st.dataframe(pd.DataFrame(event_records)[['member_name', 'status', 'recorded_at']])
