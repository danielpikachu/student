import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# 解决根目录模块导入问题
# 获取当前文件（calendar.py）所在目录的父目录（即根目录）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 将根目录添加到系统路径
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
    add_custom_css()
    st.header("📅 Event Calendar")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    calendar_sheet = None
    try:
        # 凭证文件路径（根目录下的credentials.json）
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        # 初始化Google Sheets处理器
        sheet_handler = GoogleSheetHandler(credentials_path=creds_path)
        # 获取指定工作表（表格名：StudentCouncilData，工作表名：Calendar）
        calendar_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="StudentCouncilData",
            worksheet_name="Calendar"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据到本地会话状态
    if calendar_sheet and ('calendar_events' not in st.session_state or not st.session_state.calendar_events):
        try:
            # 读取工作表所有记录
            records = sheet_handler.get_all_records(calendar_sheet)
            # 转换为本地事件格式（日期+描述）
            st.session_state.calendar_events = [
                {
                    "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                    "Description": record["Description"]
                } 
                for record in records 
                if record.get("Date") and record.get("Description")  # 过滤空记录
            ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 月份导航逻辑
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.today().replace(day=1)  # 默认为当前月1号

    # 月份切换按钮
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("← Previous", use_container_width=True, type="secondary"):
            # 计算上一个月
            prev_month = st.session_state.current_month.month - 1
            prev_year = st.session_state.current_month.year
            if prev_month == 0:  # 1月的上一个月是12月
                prev_month = 12
                prev_year -= 1
            st.session_state.current_month = datetime(prev_year, prev_month, 1)
    
    with col_title:
        st.markdown(f"### {st.session_state.current_month.strftime('%B %Y')}")  # 显示"Month Year"
    
    with col_next:
        if st.button("Next →", use_container_width=True, type="secondary"):
            # 计算下一个月
            next_month = st.session_state.current_month.month + 1
            next_year = st.session_state.current_month.year
            if next_month == 13:  # 12月的下一个月是1月
                next_month = 1
                next_year += 1
            st.session_state.current_month = datetime(next_year, next_month, 1)

    # 计算日历网格数据
    year, month = st.session_state.current_month.year, st.session_state.current_month.month
    first_day = datetime(year, month, 1)  # 当月第一天
    # 计算当月最后一天（下个月第一天减1天）
    if month < 12:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, 12, 31)
    days_in_month = last_day.day  # 当月总天数
    first_weekday = first_day.weekday()  # 当月第一天是星期几（0=周一，6=周日）

    # 映射日期到事件（便于日历渲染）
    date_events = {}
    if 'calendar_events' in st.session_state:
        for event in st.session_state.calendar_events:
            # 统一日期格式为字符串（YYYY-MM-DD）
            date_key = event["Date"].strftime("%Y-%m-%d")
            date_events[date_key] = event["Description"]

    # 渲染星期标题（周一到周日）
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # 渲染日历网格
    current_day = 1  # 从1号开始
    while current_day <= days_in_month:
        day_cols = st.columns(7)  # 每周7列
        for col_idx in range(7):
            with day_cols[col_idx]:
                # 处理月初前的空白格子
                if current_day == 1 and col_idx < first_weekday:
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                else:
                    # 处理月末后的空白格子
                    if current_day > days_in_month:
                        st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                    else:
                        # 当前日期对象
                        current_date = datetime(year, month, current_day)
                        date_key = current_date.strftime("%Y-%m-%d")
                        # 判断是否为今天
                        is_today = (current_date.date() == datetime.today().date())
                        # 判断是否有事件
                        has_event = date_key in date_events

                        # 构建样式类名
                        day_classes = "calendar-day"
                        if is_today:
                            day_classes += " calendar-day-today"
                        if has_event:
                            day_classes += " calendar-day-has-event"

                        # 事件文本（有事件则显示，否则为空）
                        event_text = f"<div class='event-text'>{date_events[date_key]}</div>" if has_event else ""

                        # 渲染日历格子
                        st.markdown(f"""
                        <div class='{day_classes}'>
                            <div class='day-number'>{current_day}</div>
                            {event_text}
                        </div>
                        """, unsafe_allow_html=True)
                        current_day += 1  # 移动到下一天

    # 事件管理面板（添加/编辑/删除事件）
    st.divider()
    with st.container(border=True):
        st.subheader("📝 Manage Calendar Events (Admin Only)")
        
        # 日期选择和事件描述输入
        col_date, col_desc = st.columns([1, 2])
        with col_date:
            selected_date = st.date_input(
                "Select Date",
                value=datetime.today(),
                label_visibility="collapsed"
            )
        
        with col_desc:
            # 自动填充已有事件（如果存在）
            event_desc = ""
            if 'calendar_events' in st.session_state:
                # 查找选中日期的事件
                existing_event = next(
                    (e for e in st.session_state.calendar_events 
                     if e["Date"] == selected_date),
                    None
                )
                if existing_event:
                    event_desc = existing_event["Description"]
            
            # 事件描述输入框
            event_desc = st.text_area(
                "Event Description (max 100 characters)",
                value=event_desc,
                max_chars=100,
                placeholder="Enter event details...",
                label_visibility="collapsed"
            )
        
        # 保存和删除按钮
        col_save, col_delete = st.columns(2)
        with col_save:
            if st.button("💾 SAVE EVENT", use_container_width=True, type="primary", key="save_event"):
                if not event_desc.strip():
                    st.error("Event description cannot be empty!")
                else:
                    # 初始化本地事件列表（如果不存在）
                    if 'calendar_events' not in st.session_state:
                        st.session_state.calendar_events = []
                    # 移除同日期的旧事件（避免重复）
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"] != selected_date
                    ]
                    # 添加新事件
                    st.session_state.calendar_events.append({
                        "Date": selected_date,
                        "Description": event_desc.strip()
                    })

                    # 同步到Google Sheets
                    if calendar_sheet and sheet_handler:
                        try:
                            # 先删除同日期的旧记录
                            sheet_handler.delete_record_by_value(
                                worksheet=calendar_sheet,
                                value=str(selected_date)  # 日期格式：YYYY-MM-DD
                            )
                            # 追加新记录（[日期, 描述]）
                            sheet_handler.append_record(
                                worksheet=calendar_sheet,
                                data=[str(selected_date), event_desc.strip()]
                            )
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")

                    st.success("✅ Event saved successfully!")
                    st.rerun()  # 刷新页面显示最新状态
        
        with col_delete:
            if st.button("🗑️ DELETE EVENT", use_container_width=True, key="delete_event"):
                if 'calendar_events' in st.session_state:
                    # 保存要删除的日期（用于同步）
                    deleted_date = selected_date
                    # 从本地事件列表中删除
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"] != deleted_date
                    ]

                    # 同步到Google Sheets（删除对应记录）
                    if calendar_sheet and sheet_handler:
                        try:
                            sheet_handler.delete_record_by_value(
                                worksheet=calendar_sheet,
                                value=str(deleted_date)
                            )
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")

                    st.success("✅ Event deleted successfully!")
                    st.rerun()  # 刷新页面显示最新状态
