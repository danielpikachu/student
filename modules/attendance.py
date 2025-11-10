# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 处理Google API错误
try:
    from googleapiclient.errors import HttpError
except ImportError:
    class HttpError(Exception):
        def __init__(self, resp, content, uri=None):
            self.resp = resp
            self.content = content
            self.uri = uri

def render_attendance():
    """渲染考勤模块界面，确保Google Sheet与界面完全一致"""
    st.set_page_config(layout="wide")
    st.header("会议考勤记录")
    st.markdown("---")

    # 初始化Google Sheets连接
    sheet_handler = None
    attendance_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        attendance_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Attendance"
        )
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")
        return  # 连接失败直接返回，避免后续错误

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
        st.session_state.last_sync_time = datetime.now()
    if "att_batch_updates" not in st.session_state:
        st.session_state.att_batch_updates = []
    if "has_pending_updates" not in st.session_state:
        st.session_state.has_pending_updates = False

    # 全量更新Google Sheets数据（覆盖模式）
    def full_update_sheets(max_retries=3):
        if not attendance_sheet or not sheet_handler:
            return False
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 准备表头
                rows = [["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]]
                
                # 准备所有考勤记录
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
                
                # 先清除所有内容再写入
                attendance_sheet.clear()
                if rows:
                    attendance_sheet.append_rows(rows, value_input_option='RAW')
                
                st.session_state.last_sync_time = datetime.now()
                st.session_state.att_batch_updates = []
                st.session_state.has_pending_updates = False
                return True
            except HttpError as e:
                if e.resp.status == 429:
                    retry_after = int(e.resp.get('retry-after', 5))
                    st.warning(f"请求频率超限，{retry_after}秒后重试...")
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

    # 应用批量更新到Google Sheets
    def apply_batch_updates():
        # 简单可靠的批量更新策略：如果有任何待更新，直接执行全量更新
        # 避免复杂的行映射逻辑导致的同步失败
        if st.session_state.has_pending_updates:
            success = full_update_sheets()
            if success:
                st.session_state.has_pending_updates = False
                st.session_state.att_batch_updates = []
                return True
        return False

    # 从Google Sheets同步数据
    def sync_from_sheets(force=False):
        if not attendance_sheet or not sheet_handler:
            return
        
        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data:
                if force:
                    st.session_state.att_members = []
                    st.session_state.att_meetings = []
                    st.session_state.att_records = {}
                return
                
            headers = all_data[0] if len(all_data) > 0 else []
            if headers != ["member_id", "member_name", "meeting_id", "meeting_name", "is_present", "updated_at"]:
                st.warning("Google Sheet格式不正确，使用本地数据")
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
            
            # 提取考勤记录
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
            
            # 更新本地状态
            st.session_state.att_meetings = meetings
            st.session_state.att_members = members
            st.session_state.att_records = records
            st.session_state.last_sync_time = datetime.now()
                
        except Exception as e:
            st.warning(f"同步失败: {str(e)}")

    # 初始同步
    if not st.session_state.att_members or not st.session_state.att_meetings:
        sync_from_sheets(force=True)

    # 渲染考勤表格
    def render_attendance_table():
        data = []
        members_to_render = st.session_state.att_members if st.session_state.att_members else [{"id": 0, "name": "无成员"}]
        
        for member in members_to_render:
            row = {"成员姓名": member["name"]}
            if st.session_state.att_meetings:
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["出勤率"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
            else:
                row["状态"] = "尚未创建会议"
                row["出勤率"] = "N/A"
            
            data.append(row)
        
        with st.container():
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

    render_attendance_table()

    # 添加手动同步按钮
    col_sync, _ = st.columns([1, 5])
    with col_sync:
        if st.button("🔄 同步数据", key="sync_button"):
            with st.spinner("正在与Google Sheet同步..."):
                # 先应用待更新
                if st.session_state.has_pending_updates:
                    apply_batch_updates()
                # 再从表格拉取最新数据
                sync_from_sheets(force=True)
                st.success("已与Google Sheet同步完成")
                st.session_state.att_needs_refresh = True

    # 自动同步待更新（每30秒）
    if st.session_state.has_pending_updates:
        if datetime.now() - st.session_state.last_sync_time > timedelta(seconds=30):
            with st.spinner("正在同步待更新内容..."):
                apply_batch_updates()
                sync_from_sheets(force=True)
                st.success("待更新内容已同步到Google Sheet")
                st.session_state.att_needs_refresh = True

    st.markdown("---")

    # 获取用户权限
    is_admin = st.session_state.get('auth_is_admin', False)

    # 仅管理员显示编辑区域
    if is_admin:
        st.header("考勤管理工具")
        col_left, col_right = st.columns(2)

        # 左列：成员导入 + 会议管理
        with col_left:
            # 1. 导入成员
            with st.container(border=True):
                st.subheader("导入成员")
                uploaded_file = st.file_uploader("上传members.xlsx", type=["xlsx"], key="member_uploader")
                import_btn = st.button("导入成员", key="att_import_members")
                
                if import_btn and uploaded_file:
                    try:
                        df = pd.read_excel(uploaded_file)
                        if "Member Name" not in df.columns:
                            st.error("Excel必须包含'Member Name'列!")
                            return
                        
                        new_members = [name.strip() for name in df["Member Name"].dropna().unique() if name.strip()]
                        added = 0
                        
                        for name in new_members:
                            if not any(m["name"] == name for m in st.session_state.att_members):
                                new_id = len(st.session_state.att_members) + 1
                                st.session_state.att_members.append({"id": new_id, "name": name})
                                for meeting in st.session_state.att_meetings:
                                    st.session_state.att_records[(new_id, meeting["id"])] = False
                                added += 1
                        
                        st.success(f"已添加{added}个新成员（将在30秒内同步）")
                        st.session_state.has_pending_updates = True
                        st.session_state.att_needs_refresh = True
                    except Exception as e:
                        st.error(f"导入失败: {str(e)}")

            # 2. 会议管理
            with st.container(border=True):
                st.subheader("管理会议")
                meeting_name = st.text_input(
                    "输入会议名称", 
                    placeholder="例如：每周例会",
                    key="att_meeting_name"
                )
                
                if st.button("添加会议", key="att_add_meeting"):
                    meeting_name = meeting_name.strip()
                    if not meeting_name:
                        st.error("请输入会议名称")
                        return
                    if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                        st.error("会议已存在")
                        return
                    
                    new_meeting_id = len(st.session_state.att_meetings) + 1
                    st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                    
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], new_meeting_id)] = False
                    
                    st.success(f"已添加会议: {meeting_name}（将在30秒内同步）")
                    st.session_state.has_pending_updates = True
                    st.session_state.att_needs_refresh = True

                if st.session_state.att_meetings:
                    selected_meeting = st.selectbox(
                        "选择要删除的会议",
                        st.session_state.att_meetings,
                        format_func=lambda x: x["name"],
                        key="att_del_meeting"
                    )
                    
                    if st.button("删除会议", key="att_delete_meeting", type="secondary"):
                        st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                        meeting_records = [(m_id, mt_id) for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id == selected_meeting["id"]]
                        for key in meeting_records:
                            del st.session_state.att_records[key]
                        
                        st.success(f"已删除会议: {selected_meeting['name']}（将在30秒内同步）")
                        st.session_state.has_pending_updates = True
                        st.session_state.att_needs_refresh = True

        # 右列：更新考勤
        with col_right.container(border=True):
            st.subheader("更新考勤")
            
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "选择会议", 
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_update_meeting"
                )
                
                if st.button("全部设为出席", key="att_set_all"):
                    for member in st.session_state.att_members:
                        st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                    
                    st.success(f"已将{selected_meeting['name']}所有人设为出席（将在30秒内同步）")
                    st.session_state.has_pending_updates = True
                    st.session_state.att_needs_refresh = True

            if st.session_state.att_members and st.session_state.att_meetings:
                selected_member = st.selectbox(
                    "选择成员",
                    st.session_state.att_members,
                    format_func=lambda x: x["name"],
                    key="att_update_member"
                )
                
                current_present = st.session_state.att_records.get((selected_member["id"], selected_meeting["id"]), False)
                is_absent = st.checkbox("缺席", value=not current_present, key="att_is_absent")
                
                if st.button("保存考勤", key="att_save_attendance"):
                    new_status = not is_absent
                    st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = new_status
                    
                    status = "缺席" if is_absent else "出席"
                    st.success(f"已将{selected_member['name']}的状态更新为{status}（将在30秒内同步）")
                    st.session_state.has_pending_updates = True
                    st.session_state.att_needs_refresh = True

        if st.session_state.has_pending_updates:
            st.info("有待更新内容将在30秒内自动同步，也可点击同步数据按钮立即同步。")
    else:
        st.info("您只有查看权限，如需修改请联系管理员。")

    # 刷新页面确保状态同步
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
