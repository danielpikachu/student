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
    ns = "calendar"  # 日历模块命名空间
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

    # 从Google Sheets同步数据到本地会话状态
    if calendar_sheet and (f"{ns}_events" not in st.session_state or not st.session_state[f"{ns}_events"]):
        try:
            all_data = calendar_sheet.get_all_values()
            
            # 检查是否有表头，没有则创建表头
            if not all_data or all_data[0] != ["date", "event"]:
                calendar_sheet.clear()
                calendar_sheet.append_row(["date", "event"])
                records = []
            else:
                records = [{"Date": row[0], "Description": row[1]} for row in all_data[1:] if row[0] and row[1]]
            
            # 转换为本地事件格式
            st.session_state[f"{ns}_events"] = [
                {
                    "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                    "Description": record["Description"]
                } 
                for record in records 
            ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 月份导航逻辑
    if f"{ns}_current_month" not in st.session_state:
        st.session_state[f"{ns}_current_month"] = datetime.today().replace(day=1)

    # 月份切换按钮
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button(
            "← Previous", 
            use_container_width=True, 
            type="secondary",
            key=f"{ns}_prev_btn"  # 前一个月按钮
        ):
            prev_month = st.session_state[f"{ns}_current_month"].month - 1
            prev_year = st.session_state[f"{ns}_current_month"].year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            st.session_state[f"{ns}_current_month"] = datetime(prev_year, prev_month, 1)
    
    with col_title:
        st.markdown(f"### {st.session_state[f'{ns}_current_month'].strftime('%B %Y')}")
    
    with col_next:
        if st.button(
            "Next →", 
            use_container_width=True, 
            type="secondary",
            key=f"{ns}_next_btn"  # 下一个月按钮
        ):
            next_month = st.session_state[f"{ns}_current_month"].month + 1
            next_year = st.session_state[f"{ns}_current_month"].year
            if next_month == 13:
                next_month = 1
                next_year += 1
            st.session_state[f"{ns}_current_month"] = datetime(next_year, next_month, 1)

    # 计算日历网格数据
    year, month = st.session_state[f"{ns}_current_month"].year, st.session_state[f"{ns}_current_month"].month
    first_day = datetime(year, month, 1)
    if month < 12:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, 12, 31)
    days_in_month = last_day.day
    first_weekday = first_day.weekday()

    # 映射日期到事件
    date_events = {}
    if f"{ns}_events" in st.session_state:
        for event in st.session_state[f"{ns}_events"]:
            date_key = event["Date"].strftime("%Y-%m-%d")
            date_events[date_key] = event["Description"]

    # 渲染星期标题
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # 渲染日历网格
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
                label_visibility="collapsed",
                key=f"{ns}_date_input"  # 日期选择器
            )
        
        with col_desc:
            event_desc = ""
            if f"{ns}_events" in st.session_state:
                existing_event = next(
                    (e for e in st.session_state[f"{ns}_events"] 
                     if e["Date"] == selected_date),
                    None
                )
                if existing_event:
                    event_desc = existing_event["Description"]
            
            event_desc = st.text_area(
                "Event Description (max 100 characters)",
                value=event_desc,
                max_chars=100,
                placeholder="Enter event details...",
                label_visibility="collapsed",
                key=f"{ns}_desc_area"  # 事件描述文本框
            )
        
        col_save, col_delete = st.columns(2)
        with col_save:
            if st.button(
                "💾 SAVE EVENT", 
                use_container_width=True, 
                type="primary", 
                key=f"{ns}_save_btn"  # 保存按钮
            ):
                if not event_desc.strip():
                    st.error("Event description cannot be empty!")
                else:
                    if f"{ns}_events" not in st.session_state:
                        st.session_state[f"{ns}_events"] = []
                    st.session_state[f"{ns}_events"] = [
                        e for e in st.session_state[f"{ns}_events"] 
                        if e["Date"] != selected_date
                    ]
                    st.session_state[f"{ns}_events"].append({
                        "Date": selected_date,
                        "Description": event_desc.strip()
                    })

                    if calendar_sheet and sheet_handler:
                        try:
                            # 删除同日期的旧记录
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(selected_date):
                                    calendar_sheet.delete_rows(i)
                            
                            # 追加新记录
                            calendar_sheet.append_row([str(selected_date), event_desc.strip()])
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")

                    st.success("✅ Event saved successfully!")
                    st.rerun()
        
        with col_delete:
            if st.button(
                "🗑️ DELETE EVENT", 
                use_container_width=True, 
                key=f"{ns}_delete_btn"  # 删除按钮
            ):
                if f"{ns}_events" in st.session_state:
                    deleted_date = selected_date
                    st.session_state[f"{ns}_events"] = [
                        e for e in st.session_state[f"{ns}_events"] 
                        if e["Date"] != deleted_date
                    ]

                    if calendar_sheet and sheet_handler:
                        try:
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(deleted_date):
                                    calendar_sheet.delete_rows(i)
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")

                    st.success("✅ Event deleted successfully!")
                    st.rerun()

if __name__ == "__main__":
    render_calendar()
