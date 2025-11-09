import os
import time
import uuid
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

# 假设 GoogleSheetHandler 和 HttpError 已正确定义
from your_google_sheet_module import GoogleSheetHandler  # 替换为实际模块路径
from some_module import HttpError  # 替换为实际模块路径

def render_attendance():
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # 初始化 Google Sheets 连接
    sheet_handler = None
    attendance_sheet = None
    try:
        # 确保 credentials.json 路径正确
        creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
        sheet_handler = GoogleSheetHandler(credentials_path=creds_path)
        attendance_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Attendance"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 初始化会话状态
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = None
    # 新增：记录本地修改，用于增量更新
    if "att_local_changes" not in st.session_state:
        st.session_state.att_local_changes = set()  # 存储 (member_id, meeting_id) 变更记录

    # 增量更新 Google Sheets 数据（仅更新变化部分）
    def incremental_update_sheets(max_retries=2):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 1. 读取现有数据（用于对比和定位行）
                existing_data = attendance_sheet.get_all_values()
                if not existing_data or existing_data[0] != [
                    "member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"
                ]:
                    # 格式不符时触发全量更新
                    st.warning("表格格式异常，触发全量同步...")
                    return full_update_sheets(max_retries=1)

                # 2. 构建现有数据索引映射（(member_id, meeting_id) -> 行号）
                row_index_map = {}
                for row_num, row in enumerate(existing_data[1:], start=2):  # 行号从2开始（跳过表头）
                    if len(row) >= 4:
                        member_id = row[0]
                        meeting_id = row[2]
                        if member_id and meeting_id:
                            row_index_map[(member_id, meeting_id)] = row_num

                # 3. 处理变更记录
                updated_count = 0
                new_rows = []
                for (member_id, meeting_id) in st.session_state.att_local_changes:
                    # 查找对应成员和会议信息
                    member = next((m for m in st.session_state.att_members if m["id"] == member_id), None)
                    meeting = next((mt for mt in st.session_state.att_meetings if mt["id"] == meeting_id), None)
                    if not member or not meeting:
                        continue

                    # 构建更新数据
                    is_present = st.session_state.att_records.get((member_id, meeting_id), False)
                    update_row = [
                        str(member_id),
                        member["name"],
                        str(meeting_id),
                        meeting["name"],
                        "TRUE" if is_present else "FALSE",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]

                    # 执行更新/插入
                    key = (str(member_id), str(meeting_id))
                    if key in row_index_map:
                        # 更新现有行
                        attendance_sheet.update(range_name=f"A{row_index_map[key]}:F{row_index_map[key]}", 
                                               values=[update_row])
                    else:
                        # 新增行
                        new_rows.append(update_row)
                    updated_count += 1

                # 批量添加新行（减少API调用）
                if new_rows:
                    attendance_sheet.append_rows(new_rows, value_input_option='RAW')

                # 4. 清空变更记录并更新同步时间
                st.session_state.att_local_changes.clear()
                st.session_state.last_sync_time = datetime.now()
                st.success(f"成功同步 {updated_count} 条变更")
                return True

            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 10))  # 延长重试间隔
                    st.warning(f"配额超限，{retry_after}秒后重试...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"更新失败: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"更新失败: {str(e)}")
                return False
        
        st.error("达到最大重试次数，同步失败")
        return False

    # 全量更新（仅在必要时使用）
    def full_update_sheets(max_retries=2):
        if not attendance_sheet or not sheet_handler:
            return True
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                rows = [["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]]
                
                for member in st.session_state.att_members:
                    if st.session_state.att_meetings:
                        for meeting in st.session_state.att_meetings:
                            is_present = st.session_state.att_records.get((member["id"], meeting["id"]), False)
                            rows.append([
                                str(member["id"]),
                                member["name"],
                                str(meeting["id"]),
                                meeting["name"],
                                "TRUE" if is_present else "FALSE",
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ])
                    else:
                        rows.append([
                            str(member["id"]),
                            member["name"],
                            "", "", "FALSE",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])

                attendance_sheet.clear()
                if rows:
                    attendance_sheet.append_rows(rows, value_input_option='RAW')
                
                st.session_state.last_sync_time = datetime.now()
                st.session_state.att_local_changes.clear()  # 清空变更记录
                return True
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 10))
                    st.warning(f"配额超限，{retry_after}秒后重试...")
                    time.sleep(retry_after)
                    retry_count += 1
                else:
                    st.error(f"全量更新失败: {str(e)}")
                    return False
            except Exception as e:
                st.error(f"全量更新失败: {str(e)}")
                return False
        
        st.error("全量更新达到最大重试次数")
        return False

    # 从 Sheets 同步数据
    def sync_from_sheets(force=False):
        if not attendance_sheet or not sheet_handler:
            return
        
        try:
            # 检查缓存是否有效（5分钟内不重复读取）
            if not force and st.session_state.last_sync_time:
                if datetime.now() - st.session_state.last_sync_time < timedelta(minutes=5):
                    st.info("使用缓存数据（5分钟内已同步）")
                    return

            all_data = attendance_sheet.get_all_values()
            if not all_data:
                if force:
                    st.session_state.att_members = []
                    st.session_state.att_meetings = []
                    st.session_state.att_records = {}
                return
                
            headers = all_data[0] if len(all_data) > 0 else []
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                st.warning("Google Sheet 格式不正确，使用本地数据")
                return

            # 提取会议数据
            meetings = []
            meeting_ids = set()
            for row in all_data[1:]:
                if len(row) >= 4 and row[2] and row[3] and row[2] not in meeting_ids:
                    meeting_ids.add(row[2])
                    try:
                        meetings.append({"id": int(row[2]), "name": row[3]})
                    except (ValueError, IndexError):
                        continue
            
            # 提取成员数据
            members = []
            member_ids = set()
            for row in all_data[1:]:
                if len(row) >= 2 and row[0] and row[1] and row[0] not in member_ids:
                    member_ids.add(row[0])
                    try:
                        members.append({"id": int(row[0]), "name": row[1]})
                    except (ValueError, IndexError):
                        continue
            
            # 提取出勤记录
            records = {}
            for row in all_data[1:]:
                if len(row) >= 5 and row[0] and row[2]:
                    try:
                        member_id = int(row[0])
                        meeting_id = int(row[2])
                        if any(m["id"] == member_id for m in members) and any(mt["id"] == meeting_id for mt in meetings):
                            records[(member_id, meeting_id)] = row[4].lower() == "true"
                    except (ValueError, IndexError):
                        continue
            
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
            st.session_state.last_sync_time = datetime.now()
            st.session_state.att_local_changes.clear()  # 同步后清空本地变更
                
        except Exception as e:
            st.warning(f"同步失败: {str(e)}")

    # 初始同步
    sync_from_sheets(force=True)

    # 渲染出勤表格
    def render_attendance_table():
        data = []
        members_to_render = st.session_state.att_members if st.session_state.att_members else [{"id": 0, "name": "No members"}]
        
        for member in members_to_render:
            row = {"Member Name": member["name"]}
            if st.session_state.att_meetings:
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
            else:
                row["Status"] = "No meetings created yet"
                row["Attendance Rates"] = "N/A"
            
            data.append(row)
        
        with st.container():
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    render_attendance_table()

    # 同步按钮
    col_sync, col_full_sync = st.columns([1, 1])
    with col_sync:
        if st.button("🔄 增量同步数据", key="sync_button"):
            with st.spinner("与 Google Sheet 同步中..."):
                sync_from_sheets(force=True)
                st.success("已与 Google Sheet 同步")
                st.session_state.att_needs_refresh = True
    with col_full_sync:
        if st.button("🔄 强制全量同步", key="full_sync_button", type="secondary"):
            with st.spinner("执行全量同步..."):
                full_update_sheets()
                st.success("全量同步完成")
                st.session_state.att_needs_refresh = True

    st.markdown("---")

    # 权限检查
    is_admin = st.session_state.get('auth_is_admin', False)

    if is_admin:
        st.header("Attendance Management Tools")
        col_left, col_right = st.columns(2)

        # 左侧：成员导入 + 会议管理
        with col_left:
            # 1. 导入成员
            with st.container(border=True):
                st.subheader("Import Members")
                uploaded_file = st.file_uploader("Upload members.xlsx", type=["xlsx"], key="member_uploader")
                import_btn = st.button("Import Members", key="att_import_members")
                
                if import_btn and uploaded_file:
                    try:
                        df = pd.read_excel(uploaded_file)
                        if "Member Name" not in df.columns:
                            st.error("Excel must have 'Member Name' column!")
                            return
                        
                        new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                        added = 0
                        
                        for name in new_members:
                            if not any(m["name"] == name for m in st.session_state.att_members):
                                new_id = len(st.session_state.att_members) + 1
                                st.session_state.att_members.append({"id": new_id, "name": name})
                                # 记录变更
                                for meeting in st.session_state.att_meetings:
                                    st.session_state.att_records[(new_id, meeting["id"])] = False
                                    st.session_state.att_local_changes.add((new_id, meeting["id"]))
                                added += 1
                        
                        st.success(f"Added {added} new members")
                        if not incremental_update_sheets():
                            st.warning("数据同步失败，请重试")
                        st.session_state.att_needs_refresh = True
                    except Exception as e:
                        st.error(f"Import failed: {str(e)}")

            # 2. 会议管理
            with st.container(border=True):
                st.subheader("Manage Meetings")
                meeting_name = st.text_input(
                    "Enter meeting name", 
                    placeholder="e.g., Weekly Sync",
                    key="att_meeting_name"
                )
                
                if st.button("Add Meeting", key="att_add_meeting"):
                    meeting_name = meeting_name.strip()
                    if not meeting_name:
                        st.error("Please enter a meeting name")
                        return
                    if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                        st.error("Meeting already exists")
                        return
                    
                    new_meeting_id = len(st.session_state.att_meetings) + 1
                    st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                    
                    # 记录变更
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], new_meeting_id)] = False
                        st.session_state.att_local_changes.add((member["id"], new_meeting_id))
                    
                    st.success(f"Added meeting: {meeting_name}")
                    if not incremental_update_sheets():
                        st.warning("数据同步失败，请重试")
                    st.session_state.att_needs_refresh = True

                # 删除会议（仍需全量更新，因为涉及多行删除）
                if st.session_state.att_meetings:
                    selected_meeting = st.selectbox(
                        "Select meeting to delete",
                        st.session_state.att_meetings,
                        format_func=lambda x: x["name"],
                        key="att_del_meeting"
                    )
                    
                    if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                        st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                        # 收集需要删除的记录
                        to_remove = [(m_id, mt_id) for (m_id, mt_id) in st.session_state.att_records if mt_id == selected_meeting["id"]]
                        for key in to_remove:
                            del st.session_state.att_records[key]
                        # 清空变更记录并触发全量更新
                        st.session_state.att_local_changes.clear()
                        
                        st.success(f"Deleted meeting: {selected_meeting['name']}")
                        if not full_update_sheets():
                            st.warning("数据同步失败，请重试")
                        st.session_state.att_needs_refresh = True

        # 右侧：更新出勤
        with col_right.container(border=True):
            st.subheader("Update Attendance")
            
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "Select Meeting", 
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_update_meeting"
                )
                
                # 一键全到
                if st.button("Set All Present", key="att_set_all"):
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                        st.session_state.att_local_changes.add((member["id"], selected_meeting["id"]))
                    
                    st.success(f"All present for {selected_meeting['name']}")
                    if not incremental_update_sheets():
                        st.warning("数据同步失败，请重试")
                    st.session_state.att_needs_refresh = True

            # 单独更新成员状态
            if st.session_state.att_members and st.session_state.att_meetings:
                selected_member = st.selectbox(
                    "Select Member",
                    st.session_state.att_members,
                    format_func=lambda x: x["name"],
                    key="att_update_member"
                )
                
                current_present = st.session_state.att_records.get((selected_member["id"], selected_meeting["id"]), False)
                is_absent = st.checkbox("Absent", value=not current_present, key="att_is_absent")

                
                if st.button("Save Attendance", key="att_save_attendance"):
                    new_status = not is_absent
                    st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = new_status
                    st.session_state.att_local_changes.add((selected_member["id"], selected_meeting["id"]))
                    
                    status = "absent" if is_absent else "present"
                    st.success(f"Updated {selected_member['name']}'s status to {status}")
                    if not incremental_update_sheets():
                        st.warning("数据同步失败，请重试")
                    st.session_state.att_needs_refresh = True
    else:
        st.info("You have view-only access. Please contact an administrator for changes.")

    # 刷新页面确保状态同步
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
