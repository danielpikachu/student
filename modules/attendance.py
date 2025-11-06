# modules/attendance.py
import streamlit as st
import pandas as pd
from datetime import datetime
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
    """渲染考勤模块界面（增强版同步逻辑）"""
    st.set_page_config(layout="wide")
    st.header("Meeting Attendance Records")
    st.markdown("---")

    # 初始化Google Sheets连接
    sheet_handler = None
    attendance_sheet = None
    sheet_available = False  # 标记Sheet是否可用
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        
        # 尝试获取或创建工作表
        try:
            attendance_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Attendance"
            )
            sheet_available = True
            st.success("已成功连接到Attendance工作表")
        except Exception as e:
            st.info(f"尝试创建新的Attendance工作表: {str(e)}")
            # 尝试创建工作表（兼容不同实现）
            if hasattr(sheet_handler, 'create_worksheet'):
                attendance_sheet = sheet_handler.create_worksheet(
                    spreadsheet_name="Student",
                    worksheet_name="Attendance",
                    rows=1000,
                    cols=50
                )
                sheet_available = True
                st.success("已创建新的Attendance工作表")
            else:
                st.error("GoogleSheetHandler不支持创建工作表，请手动创建名为'Attendance'的工作表")
    except Exception as e:
        st.error(f"Google Sheets连接失败: {str(e)}")

    # 初始化会话状态
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "att_needs_refresh" not in st.session_state:
        st.session_state.att_needs_refresh = False

    # 强制同步数据到Google Sheet（核心修复）
    def force_sync_to_sheet():
        if not sheet_available or not attendance_sheet:
            st.warning("无法同步到Google Sheet：连接不可用")
            return False

        try:
            # 1. 准备完整的表格数据（与界面完全一致）
            interface_columns = ["Member Name"]
            meeting_names = [m["name"] for m in st.session_state.att_meetings]
            interface_columns.extend(meeting_names)
            interface_columns.append("Attendance Rates")

            # 2. 清空整个工作表（确保没有旧数据残留）
            attendance_sheet.clear()
            time.sleep(1)  # 等待清除完成

            # 3. 写入表头
            attendance_sheet.append_row(interface_columns)
            time.sleep(1)

            # 4. 写入成员数据
            if st.session_state.att_members:
                sheet_data = []
                for member in st.session_state.att_members:
                    row = [member["name"]]
                    # 各会议出勤状态
                    for meeting in st.session_state.att_meetings:
                        row.append("✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗")
                    # 出勤率
                    attended_count = sum(1 for m in st.session_state.att_meetings 
                                       if st.session_state.att_records.get((member["id"], m["id"]), False))
                    total_meetings = len(st.session_state.att_meetings)
                    rate = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                    row.append(rate)
                    sheet_data.append(row)

                # 批量写入所有成员数据
                attendance_sheet.append_rows(sheet_data)
                time.sleep(1)

                # 5. 设置格式（加粗表头、调整列宽）
                attendance_sheet.format("1:1", {"textFormat": {"bold": True}})
                # 自动调整列宽
                for col_idx in range(1, len(interface_columns) + 1):
                    attendance_sheet.set_column_width(col_idx, 150)  # 150像素宽度

            st.success("✅ 已成功同步到Google Sheet")
            return True

        except HttpError as e:
            st.error(f"Google API错误: {str(e)}")
            if e.resp.status == 403:
                st.info("可能是权限问题，请检查Google Sheets API权限设置")
            elif e.resp.status == 429:
                st.info("请求过于频繁，请1分钟后再试")
            return False
        except Exception as e:
            st.error(f"同步失败: {str(e)}")
            return False

    # 从Google Sheet同步数据到本地
    def sync_from_sheet():
        if not sheet_available or not attendance_sheet:
            return

        try:
            all_data = attendance_sheet.get_all_values()
            if not all_data or len(all_data) < 1:
                st.info("Google Sheet中没有数据")
                return

            # 解析表头
            headers = all_data[0]
            if not headers or headers[0] != "Member Name":
                st.warning("Google Sheet表头格式不正确，预期第一列为'Member Name'")
                return

            # 提取会议名称（表头第2列到倒数第2列）
            meeting_names = headers[1:-1] if len(headers) > 2 else []
            st.session_state.att_meetings = [
                {"id": i + 1, "name": name} 
                for i, name in enumerate(meeting_names)
            ]

            # 提取成员和考勤记录
            members = []
            records = {}
            for row in all_data[1:]:  # 从第2行开始
                if not row or not row[0]:
                    continue  # 跳过空行

                member_name = row[0].strip()
                member_id = len(members) + 1
                members.append({"id": member_id, "name": member_name})

                # 解析每个会议的出勤状态
                for meeting_idx, meeting in enumerate(st.session_state.att_meetings):
                    if meeting_idx + 1 < len(row):
                        status = row[meeting_idx + 1].strip()
                        records[(member_id, meeting["id"])] = (status == "✓")

            st.session_state.att_members = members
            st.session_state.att_records = records
            st.success("✅ 已从Google Sheet加载数据")

        except Exception as e:
            st.warning(f"从Sheet加载数据失败: {str(e)}")

    # 初始同步（先从Sheet加载）
    if not st.session_state.att_members or not st.session_state.att_meetings:
        sync_from_sheet()

    # 渲染考勤表格
    def render_attendance_table():
        if st.session_state.att_members and st.session_state.att_meetings:
            data = []
            for member in st.session_state.att_members:
                row = {"Member Name": member["name"]}
                for meeting in st.session_state.att_meetings:
                    row[meeting["name"]] = "✓" if st.session_state.att_records.get((member["id"], meeting["id"]), False) else "✗"
                # 计算出勤率
                attended_count = sum(1 for m in st.session_state.att_meetings 
                                   if st.session_state.att_records.get((member["id"], m["id"]), False))
                total_meetings = len(st.session_state.att_meetings)
                row["Attendance Rates"] = f"{(attended_count / total_meetings * 100):.1f}%" if total_meetings > 0 else "0%"
                data.append(row)
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            return data
        else:
            st.info("没有成员或会议数据，请先添加")
            return None

    # 渲染表格
    table_data = render_attendance_table()

    st.markdown("---")

    # 操作区域布局
    st.header("Attendance Management Tools")
    col_left, col_right = st.columns(2)

    # 左侧：成员导入 + 会议管理
    with col_left:
        # 1. 导入成员
        with st.container(border=True):
            st.subheader("Import Members")
            if st.button("Import from members.xlsx", key="att_import_members"):
                try:
                    df = pd.read_excel("members.xlsx")
                    if "Member Name" not in df.columns:
                        st.error("Excel必须包含'Member Name'列")
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
                    
                    st.success(f"已添加 {added} 个新成员")
                    if sheet_available:
                        force_sync_to_sheet()  # 强制同步到Sheet
                    st.session_state.att_needs_refresh = True
                except Exception as e:
                    st.error(f"导入失败: {str(e)}")

        # 2. 会议管理
        with st.container(border=True):
            st.subheader("Manage Meetings")
            # 添加会议
            meeting_name = st.text_input(
                "输入会议名称", 
                placeholder="例如：周会",
                key="att_meeting_name"
            )
            
            if st.button("Add Meeting", key="att_add_meeting"):
                meeting_name = meeting_name.strip()
                if not meeting_name:
                    st.error("请输入会议名称")
                    return
                if any(m["name"] == meeting_name for m in st.session_state.att_meetings):
                    st.error("该会议已存在")
                    return
                
                new_meeting_id = len(st.session_state.att_meetings) + 1
                st.session_state.att_meetings.append({"id": new_meeting_id, "name": meeting_name})
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], new_meeting_id)] = False
                
                st.success(f"已添加会议: {meeting_name}")
                if sheet_available:
                    force_sync_to_sheet()  # 强制同步到Sheet
                st.session_state.att_needs_refresh = True

            # 删除会议
            if st.session_state.att_meetings:
                selected_meeting = st.selectbox(
                    "选择要删除的会议",
                    st.session_state.att_meetings,
                    format_func=lambda x: x["name"],
                    key="att_del_meeting"
                )
                
                if st.button("Delete Meeting", key="att_delete_meeting", type="secondary"):
                    st.session_state.att_meetings = [m for m in st.session_state.att_meetings if m["id"] != selected_meeting["id"]]
                    st.session_state.att_records = {(m_id, mt_id): v for (m_id, mt_id), v in st.session_state.att_records.items() if mt_id != selected_meeting["id"]}
                    
                    st.success(f"已删除会议: {selected_meeting['name']}")
                    if sheet_available:
                        force_sync_to_sheet()  # 强制同步到Sheet
                    st.session_state.att_needs_refresh = True

    # 右侧：更新考勤 + 强制同步按钮
    with col_right.container(border=True):
        st.subheader("Update Attendance")
        
        # 强制同步按钮（手动触发）
        if st.button("🔄 强制同步到Google Sheet", key="att_force_sync"):
            force_sync_to_sheet()
        
        if st.session_state.att_meetings:
            selected_meeting = st.selectbox(
                "选择会议", 
                st.session_state.att_meetings,
                format_func=lambda x: x["name"],
                key="att_update_meeting"
            )
            
            # 一键全到
            if st.button("Set All Present", key="att_set_all"):
                for member in st.session_state.att_members:
                    st.session_state.att_records[(member["id"], selected_meeting["id"])] = True
                
                st.success(f"所有成员已标记为出席: {selected_meeting['name']}")
                if sheet_available:
                    force_sync_to_sheet()  # 强制同步到Sheet
                st.session_state.att_needs_refresh = True

        # 单独更新成员状态
        if st.session_state.att_members and st.session_state.att_meetings:
            selected_member = st.selectbox(
                "选择成员",
                st.session_state.att_members,
                format_func=lambda x: x["name"],
                key="att_update_member"
            )
            
            current_status = st.session_state.att_records.get((selected_member["id"], selected_meeting["id"]), False)
            is_present = st.checkbox("出席", value=current_status, key="att_is_present")
            
            if st.button("保存考勤", key="att_save_attendance"):
                st.session_state.att_records[(selected_member["id"], selected_meeting["id"])] = is_present
                
                st.success(f"已更新 {selected_member['name']} 的考勤状态")
                if sheet_available:
                    force_sync_to_sheet()  # 强制同步到Sheet
                st.session_state.att_needs_refresh = True

    # 刷新界面
    if st.session_state.att_needs_refresh:
        st.session_state.att_needs_refresh = False
        st.rerun()
