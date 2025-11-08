# modules/calendar.py
import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 自定义CSS样式
def add_custom_css():
    st.markdown("""
    <style>
    .calendar-day {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        min-height: 100px;
        margin: 5px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .calendar-day-today {
        border: 2px solid #ff4b4b;
        background-color: #fff5f5;
    }
    .calendar-day-has-event {
        border: 2px solid #4b8bff;
    }
    .day-number {
        font-weight: bold;
        margin-bottom: 5px;
    }
    .event-text {
        font-size: 0.85rem;
        color: #555;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .weekday-label {
        text-align: center;
        font-weight: bold;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

def render_calendar():
    """渲染日历模块界面（cal_前缀命名空间）"""
    add_custom_css()
    st.header("📅 Event Calendar")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    calendar_sheet = None
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        sheet_handler = GoogleSheetHandler(credentials_path=creds_path)
        calendar_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Calendar"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据（使用cal_events状态）
    if calendar_sheet and sheet_handler:
        try:
            all_data = calendar_sheet.get_all_values()
            expected_headers = ["date", "event"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                calendar_sheet.clear()
                calendar_sheet.append_row(expected_headers)
                records = []
            else:
                # 处理数据（跳过表头）
                records = [
                    {"date": row[0], "event": row[1]} 
                    for row in all_data[1:] 
                    if row[0] and row[1]  # 确保日期和事件都不为空
                ]
            
            # 转换为datetime格式并更新会话状态
            st.session_state.cal_events = [
                {
                    "date": datetime.strptime(record["date"], "%Y-%m-%d").date(),
                    "description": record["event"]
                } 
                for record in records
            ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # ---------------------- 月份导航 ----------------------
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if st.button("← Previous Month", use_container_width=True, type="secondary", key="cal_btn_prev_month"):
            # 计算上一个月
            current = st.session_state.cal_current_month
            prev_month = current.month - 1
            prev_year = current.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            st.session_state.cal_current_month = datetime(prev_year, prev_month, 1)
    
    with col_title:
        st.markdown(f"### {st.session_state.cal_current_month.strftime('%B %Y')}")
    
    with col_next:
        if st.button("Next Month →", use_container_width=True, type="secondary", key="cal_btn_next_month"):
            # 计算下一个月
            current = st.session_state.cal_current_month
            next_month = current.month + 1
            next_year = current.year
            if next_month == 13:
                next_month = 1
                next_year += 1
            st.session_state.cal_current_month = datetime(next_year, next_month, 1)

    # ---------------------- 日历网格计算 ----------------------
    year, month = st.session_state.cal_current_month.year, st.session_state.cal_current_month.month
    first_day = datetime(year, month, 1)
    
    # 计算当月最后一天
    if month < 12:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, 12, 31)
    
    days_in_month = last_day.day
    first_weekday = first_day.weekday()  # 0=周一, 6=周日

    # 构建日期-事件映射
    date_event_map = {}
    for event in st.session_state.cal_events:
        date_key = event["date"].strftime("%Y-%m-%d")
        date_event_map[date_key] = event["description"]

    # ---------------------- 渲染日历网格 ----------------------
    # 渲染星期标题
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # 渲染日期网格
    current_day = 1
    while current_day <= days_in_month:
        day_cols = st.columns(7)
        for col_idx in range(7):
            with day_cols[col_idx]:
                # 处理月初前的空白单元格
                if current_day == 1 and col_idx < first_weekday:
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                elif current_day > days_in_month:
                    # 处理月末后的空白单元格
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                else:
                    # 渲染有效日期单元格
                    current_date = datetime(year, month, current_day).date()
                    date_key = current_date.strftime("%Y-%m-%d")
                    is_today = (current_date == datetime.today().date())
                    has_event = date_key in date_event_map

                    # 构建CSS类
                    day_classes = "calendar-day"
                    if is_today:
                        day_classes += " calendar-day-today"
                    if has_event:
                        day_classes += " calendar-day-has-event"

                    # 构建事件文本
                    event_text = f"<div class='event-text'>{date_event_map[date_key]}</div>" if has_event else ""

                    # 渲染单元格
                    st.markdown(f"""
                    <div class='{day_classes}'>
                        <div class='day-number'>{current_day}</div>
                        {event_text}
                    </div>
                    """, unsafe_allow_html=True)

                    current_day += 1

    # ---------------------- 事件管理面板（仅管理员可见） ----------------------
    st.divider()
    # 仅管理员显示编辑区域
    if st.session_state.auth_is_admin:
        with st.container(border=True):
            st.subheader("📝 Manage Calendar Events")
            
            # 事件编辑区域（移除了密码验证）
            col_date, col_desc = st.columns([1, 2])
            
            with col_date:
                selected_date = st.date_input(
                    "Select Date",
                    value=datetime.today(),
                    label_visibility="collapsed",
                    key="cal_input_event_date"
                )
            
            with col_desc:
                # 检查选中日期是否已有事件
                existing_event = next(
                    (e for e in st.session_state.cal_events if e["date"] == selected_date),
                    None
                )
                default_desc = existing_event["description"] if existing_event else ""
                
                event_desc = st.text_area(
                    "Event Description (max 100 characters)",
                    value=default_desc,
                    max_chars=100,
                    placeholder="Enter event details...",
                    label_visibility="collapsed",
                    key="cal_input_event_desc"
                )
            
            # 操作按钮
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("💾 Save Event", use_container_width=True, type="primary", key="cal_btn_save_event"):
                    if not event_desc.strip():
                        st.error("Event description cannot be empty!")
                        return
                    
                    # 删除同日期的旧事件
                    st.session_state.cal_events = [
                        e for e in st.session_state.cal_events 
                        if e["date"] != selected_date
                    ]
                    
                    # 添加新事件
                    new_event = {
                        "date": selected_date,
                        "description": event_desc.strip()
                    }
                    st.session_state.cal_events.append(new_event)
                    
                    # 同步到Google Sheets
                    if calendar_sheet and sheet_handler:
                        try:
                            # 删除旧记录
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(selected_date):
                                    calendar_sheet.delete_rows(i)
                            
                            # 添加新记录
                            calendar_sheet.append_row([str(selected_date), event_desc.strip()])
                            st.success("✅ Event saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")
            
            with col_delete:
                if st.button("🗑️ Delete Event", use_container_width=True, key="cal_btn_delete_event"):
                    if not existing_event:
                        st.warning("No event found for this date!")
                        return
                    
                    # 删除本地事件
                    st.session_state.cal_events = [
                        e for e in st.session_state.cal_events 
                        if e["date"] != selected_date
                    ]
                    
                    # 同步删除Google Sheets记录
                    if calendar_sheet and sheet_handler:
                        try:
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(selected_date):
                                    calendar_sheet.delete_rows(i)
                            st.success("✅ Event deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")
