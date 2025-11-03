import streamlit as st
import pandas as pd
from datetime import datetime
import os

def render_attendance():
    st.header("Attendance Management Tools")  # 匹配图片标题

    # 初始化会话状态（补充成员ID生成逻辑，避免重复）
    if 'attendance_events' not in st.session_state:
        st.session_state.attendance_events = []
    if 'attendance_records' not in st.session_state:
        st.session_state.attendance_records = []
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'next_member_id' not in st.session_state:  # 用于手动添加成员时生成唯一ID
        st.session_state.next_member_id = 1

    # ---------------------- 1. 成员管理模块（匹配图片"Add New Member"和"Import Members"）----------------------
    st.subheader("Member Management")
    tab1, tab2 = st.tabs(["Add New Member", "Import Members from Excel"])

    # 手动添加成员（图片"Add New Member"功能）
    with tab1:
        with st.form("add_new_member_form"):
            member_name = st.text_input("Member Name", placeholder="Enter member's full name")
            submit_member = st.form_submit_button("Add Member")
            
            if submit_member and member_name.strip():
                # 检查成员是否已存在（避免重复添加）
                existing_names = [m["name"].strip().lower() for m in st.session_state.members]
                if member_name.strip().lower() in existing_names:
                    st.warning(f"Member '{member_name}' already exists!")
                else:
                    # 添加新成员（包含唯一ID）
                    new_member = {
                        "id": st.session_state.next_member_id,
                        "name": member_name.strip()
                    }
                    st.session_state.members.append(new_member)
                    st.session_state.next_member_id += 1  # 更新下一个ID
                    st.success(f"Member '{member_name}' added successfully!")

    # 导入成员列表（保留原功能，匹配图片"Import Members from Excel"）
    with tab2:
        member_file = st.file_uploader("Upload Member List (Excel)", type=["xlsx", "xls"])
        if member_file:
            try:
                df = pd.read_excel(member_file)
                # 确保Excel包含"name"列，若有"id"列则复用，无则生成唯一ID
                if "name" not in df.columns:
                    st.error("Excel file must contain a 'name' column!")
                else:
                    # 处理ID列（若不存在则从next_member_id开始生成）
                    if "id" not in df.columns:
                        df["id"] = range(
                            st.session_state.next_member_id,
                            st.session_state.next_member_id + len(df)
                        )
                        st.session_state.next_member_id += len(df)
                    # 转换为字典并更新成员列表（去重）
                    new_members = df[["id", "name"]].drop_duplicates(subset=["name"]).to_dict('records')
                    existing_ids = {m["id"] for m in st.session_state.members}
                    added_count = 0
                    for m in new_members:
                        if m["id"] not in existing_ids and m["name"].strip():
                            st.session_state.members.append(m)
                            existing_ids.add(m["id"])
                            added_count += 1
                    st.success(f"Loaded {added_count} new members successfully!")
                    st.dataframe(df[["id", "name"]])
            except Exception as e:
                st.error(f"Error loading member list: {str(e)}")

    # 显示当前成员列表（方便查看和后续操作）
    if st.session_state.members:
        st.subheader("Current Member List")
        members_df = pd.DataFrame(st.session_state.members)
        st.dataframe(members_df[["id", "name"]], hide_index=True)


    # ---------------------- 2. 会议管理模块（匹配图片"Add New Meeting"和"Delete Meeting"）----------------------
    st.subheader("Meeting Management")
    tab3, tab4 = st.tabs(["Add New Meeting", "Delete Meeting"])

    # 添加新会议（匹配图片"Add New Meeting"功能）
    with tab3:
        with st.form("new_meeting_form"):
            event_name = st.text_input("Meeting Name", placeholder="e.g., First Semester Meeting")
            event_date = st.date_input("Meeting Date", datetime.today())
            event_time = st.time_input("Meeting Time")
            submit_event = st.form_submit_button("Add Meeting")
            
            if submit_event and event_name.strip():
                # 生成唯一会议ID
                event_id = len(st.session_state.attendance_events) + 1
                new_event = {
                    "id": event_id,
                    "name": event_name.strip(),
                    "date": event_date,
                    "time": event_time,
                    "created_at": datetime.now()
                }
                st.session_state.attendance_events.append(new_event)
                st.success(f"Meeting '{event_name}' added successfully!")

    # 删除会议（匹配图片"Select Meeting to Delete"功能）
    with tab4:
        if st.session_state.attendance_events:
            # 选择要删除的会议
            selected_del_event = st.selectbox(
                "Select Meeting to Delete",
                st.session_state.attendance_events,
                format_func=lambda x: f"{x['name']} - {x['date']} {x['time']}"
            )
            if st.button("Delete Meeting", type="primary", help="This will also delete related attendance records"):
                # 删除会议及关联的考勤记录
                event_id_to_del = selected_del_event["id"]
                st.session_state.attendance_events = [
                    e for e in st.session_state.attendance_events if e["id"] != event_id_to_del
                ]
                st.session_state.attendance_records = [
                    r for r in st.session_state.attendance_records if r["event_id"] != event_id_to_del
                ]
                st.success(f"Meeting '{selected_del_event['name']}' deleted successfully!")
        else:
            st.info("No meetings available to delete")


    # ---------------------- 3. 考勤操作模块（匹配图片"Quick Actions"和"Mark All Present"）----------------------
    st.subheader("Attendance Operations")
    if st.session_state.attendance_events and st.session_state.members:
        # 选择会议（匹配图片"Select Meeting"）
        selected_event = st.selectbox(
            "Select Meeting to Take Attendance",
            st.session_state.attendance_events,
            format_func=lambda x: f"{x['name']} - {x['date']} {x['time']}"
        )
        event_id = selected_event["id"]
        event_name = selected_event["name"]

        # 过滤该会议的现有考勤记录
        event_records = [r for r in st.session_state.attendance_records if r["event_id"] == event_id]

        # 快速操作：一键标记全部在场（匹配图片"Mark All Present"）
        col_quick1, col_quick2 = st.columns(2)
        with col_quick1:
            if st.button("Mark All Present", help="Set all members' status to 'Present'"):
                # 生成全部在场的考勤数据
                attendance_data = [
                    {"member": m, "status": "Present"} for m in st.session_state.members
                ]
                # 更新考勤记录
                st.session_state.attendance_records = [
                    r for r in st.session_state.attendance_records if r["event_id"] != event_id
                ]
                for data in attendance_data:
                    st.session_state.attendance_records.append({
                        "event_id": event_id,
                        "event_name": event_name,
                        "member_id": data["member"]["id"],
                        "member_name": data["member"]["name"],
                        "status": data["status"],
                        "recorded_at": datetime.now()
                    })
                st.success(f"All members marked as 'Present' for {event_name}!")

        # 手动调整考勤状态
        st.write(f"Adjust Attendance for: **{event_name}**")
        with st.form(f"attendance_form_{event_id}"):
            attendance_data = []
            # 按成员ID排序，确保显示顺序一致
            sorted_members = sorted(st.session_state.members, key=lambda x: x["id"])
            for member in sorted_members:
                member_id = member["id"]
                member_name = member["name"]
                
                # 读取现有状态（无记录则默认"Present"）
                default_status = "Present"
                for record in event_records:
                    if record["member_id"] == member_id:
                        default_status = record["status"]
                        break
                
                # 选择考勤状态（Present/Absent/Late）
                status = st.radio(
                    f"Status for {member_name}",
                    ["Present", "Absent", "Late"],
                    index=["Present", "Absent", "Late"].index(default_status),
                    key=f"attendance_{event_id}_{member_id}"
                )
                attendance_data.append({"member": member, "status": status})
            
            submit_attendance = st.form_submit_button("Save Attendance Adjustments")
            if submit_attendance:
                # 删除旧记录，保存新记录
                st.session_state.attendance_records = [
                    r for r in st.session_state.attendance_records if r["event_id"] != event_id
                ]
                for data in attendance_data:
                    st.session_state.attendance_records.append({
                        "event_id": event_id,
                        "event_name": event_name,
                        "member_id": data["member"]["id"],
                        "member_name": data["member"]["name"],
                        "status": data["status"],
                        "recorded_at": datetime.now()
                    })
                st.success(f"Attendance for {event_name} saved successfully!")

        # 考勤统计（保留原功能，优化显示）
        if event_records:
            st.subheader("Attendance Statistics")
            present_count = sum(1 for r in event_records if r["status"] == "Present")
            absent_count = sum(1 for r in event_records if r["status"] == "Absent")
            late_count = sum(1 for r in event_records if r["status"] == "Late")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Present", present_count, f"{(present_count/len(event_records)*100):.1f}%")
            col2.metric("Absent", absent_count, f"{(absent_count/len(event_records)*100):.1f}%")
            col3.metric("Late", late_count, f"{(late_count/len(event_records)*100):.1f}%")
            
            # 详细记录（隐藏event_id等冗余字段）
            st.subheader("Detailed Attendance Records")
            records_df = pd.DataFrame(event_records)[["member_name", "status", "recorded_at"]]
            records_df["recorded_at"] = pd.to_datetime(records_df["recorded_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(records_df, hide_index=True)


    # ---------------------- 4. 数据管理模块（匹配图片"Remove Member"和"Reset Attendance Data"）----------------------
    st.subheader("Data Management")
    col_data1, col_data2 = st.columns(2)

    # 移除成员（匹配图片"Select Member to Remove"）
    with col_data1:
        st.subheader("Remove Member")
        if st.session_state.members:
            selected_member = st.selectbox(
                "Select Member to Remove",
                st.session_state.members,
                format_func=lambda x: f"{x['name']} (ID: {x['id']})"
            )
            if st.button("Remove Member", type="primary", help="This will not delete existing attendance records"):
                # 移除成员（保留历史考勤记录，仅从成员列表删除）
                member_id_to_del = selected_member["id"]
                st.session_state.members = [
                    m for m in st.session_state.members if m["id"] != member_id_to_del
                ]
                # 更新next_member_id（避免ID重复）
                if st.session_state.members:
                    st.session_state.next_member_id = max(m["id"] for m in st.session_state.members) + 1
                else:
                    st.session_state.next_member_id = 1
                st.success(f"Member '{selected_member['name']}' removed successfully!")
        else:
            st.info("No members available to remove")

    # 重置考勤数据（匹配图片"Reset Attendance Data"）
    with col_data2:
        st.subheader("Reset Attendance Data")
        st.warning("Warning: This will delete ALL attendance records (meetings and members will be kept)!")
        if st.button("Reset Attendance Records", type="primary", disabled=not st.session_state.attendance_records):
            st.session_state.attendance_records = []
            st.success("All attendance records have been reset!")

    # 重置所有数据（补充功能，方便测试）
    st.subheader("Full Data Reset (For Testing)")
    st.error("DANGER: This will delete ALL data (members, meetings, attendance records)!")
    if st.button("Reset All Data", type="primary", disabled=not (st.session_state.members or st.session_state.attendance_events or st.session_state.attendance_records)):
        st.session_state.attendance_events = []
        st.session_state.attendance_records = []
        st.session_state.members = []
        st.session_state.next_member_id = 1
        st.success("All data has been reset!")


# 执行考勤管理界面渲染
if __name__ == "__main__":
    render_attendance()
