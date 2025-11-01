import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# 更可靠的路径配置：获取根目录绝对路径
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 确保根目录只被添加一次
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)  # 插入到路径列表最前面，优先搜索

# 现在可以安全导入
import gspread
from google.oauth2.service_account import Credentials
from google_sheet_utils import get_worksheet  # 根目录模块

# 自定义样式
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

    # Google Sheets初始化
    SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
    sheet = None
    try:
        # 明确指定credentials.json的根目录路径
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPE
        )
        client = gspread.authorize(creds)
        
        sheet = get_worksheet(client, "StudentCouncilData", "Calendar")
        
        if 'calendar_events' not in st.session_state or not st.session_state.calendar_events:
            records = sheet.get_all_records()
            st.session_state.calendar_events = [
                {
                    "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                    "Description": record["Description"]
                } 
                for record in records 
                if record["Date"] and record["Description"]
            ]
    except Exception as e:
        st.error(f"Google Sheets连接错误: {str(e)}")

    # 月份初始化
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.today().replace(day=1)

    # 月份切换
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("← Previous", use_container_width=True, type="secondary"):
            prev_month = st.session_state.current_month.month - 1
            prev_year = st.session_state.current_month.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            st.session_state.current_month = datetime(prev_year, prev_month, 1)
    
    with col_title:
        st.markdown(f"### {st.session_state.current_month.strftime('%B %Y')}")
    
    with col_next:
        if st.button("Next →", use_container_width=True, type="secondary"):
            next_month = st.session_state.current_month.month + 1
            next_year = st.session_state.current_month.year
            if next_month == 13:
                next_month = 1
                next_year += 1
            st.session_state.current_month = datetime(next_year, next_month, 1)

    # 日历数据计算
    year, month = st.session_state.current_month.year, st.session_state.current_month.month
    first_day = datetime(year, month, 1)
    last_day = (datetime(year, month+1, 1) - timedelta(days=1)) if month < 12 else datetime(year, 12, 31)
    days_in_month = last_day.day
    first_weekday = first_day.weekday()

    # 事件数据映射
    date_events = {}
    if 'calendar_events' in st.session_state:
        for event in st.session_state.calendar_events:
            if isinstance(event["Date"], datetime):
                date_obj = event["Date"]
            else:
                date_obj = datetime.combine(event["Date"], datetime.min.time())
            date_key = date_obj.strftime("%Y-%m-%d")
            date_events[date_key] = event["Description"]

    # 星期标题
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # 绘制日历网格
    current_day = 1
    while current_day <= days_in_month:
        day_cols = st.columns(7)
        for col_idx in range(7):
            with day_cols[col_idx]:
                if current_day == 1 and col_idx < first_weekday:
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                else:
                    if current_day > days_in_month:
                        st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                    else:
                        current_date = datetime(year, month, current_day)
                        date_key = current_date.strftime("%Y-%m-%d")
                        is_today = (current_date.date() == datetime.today().date())
                        has_event = date_key in date_events

                        day_classes = "calendar-day"
                        if is_today:
                            day_classes += " calendar-day-today"
                        if has_event:
                            day_classes += " calendar-day-has-event"

                        event_text = f"<div class='event-text'>{date_events[date_key]}</div>" if has_event else ""

                        st.markdown(f"""
                        <div class='{day_classes}'>
                            <div class='day-number'>{current_day}</div>
                            {event_text}
                        </div>
                        """, unsafe_allow_html=True)
                        current_day += 1

    # 事件管理面板
    st.divider()
    with st.container(border=True):
        st.subheader("📝 Manage Calendar Events (Admin Only)")
        
        col_date, col_desc = st.columns([1, 2])
        with col_date:
            selected_date = st.date_input(
                "Select Date",
                value=datetime.today(),
                label_visibility="collapsed"
            )
        
        with col_desc:
            event_desc = ""
            if 'calendar_events' in st.session_state:
                selected_date_obj = selected_date if isinstance(selected_date, datetime) else datetime.combine(selected_date, datetime.min.time())
                existing = next(
                    (e for e in st.session_state.calendar_events 
                     if (e["Date"].date() if isinstance(e["Date"], datetime) else e["Date"]) == selected_date),
                    None
                )
                if existing:
                    event_desc = existing["Description"]
            
            event_desc = st.text_area(
                "Event Description (max 100 characters)",
                value=event_desc,
                max_chars=100,
                placeholder="Enter event details...",
                label_visibility="collapsed"
            )
        
        col_save, col_delete = st.columns(2)
        with col_save:
            if st.button("💾 SAVE EVENT", use_container_width=True, type="primary", key="save_event"):
                if not event_desc.strip():
                    st.error("Event description cannot be empty!")
                else:
                    if 'calendar_events' not in st.session_state:
                        st.session_state.calendar_events = []
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if (e["Date"].date() if isinstance(e["Date"], datetime) else e["Date"]) != selected_date
                    ]
                    st.session_state.calendar_events.append({
                        "Date": selected_date,
                        "Description": event_desc.strip()
                    })

                    if sheet:
                        try:
                            cell = sheet.find(str(selected_date))
                            if cell:
                                sheet.delete_rows(cell.row)
                            sheet.append_row([str(selected_date), event_desc.strip()])
                        except gspread.exceptions.CellNotFound:
                            sheet.append_row([str(selected_date), event_desc.strip()])
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")

                    st.success("✅ Event saved successfully!")
                    st.rerun()
        
        with col_delete:
            if st.button("🗑️ DELETE EVENT", use_container_width=True, key="delete_event"):
                if 'calendar_events' in st.session_state:
                    deleted_date = selected_date
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if (e["Date"].date() if isinstance(e["Date"], datetime) else e["Date"]) != selected_date
                    ]

                    if sheet:
                        try:
                            cell = sheet.find(str(deleted_date))
                            if cell:
                                sheet.delete_rows(cell.row)
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")

                    st.success("✅ Event deleted successfully!")
                    st.rerun()
