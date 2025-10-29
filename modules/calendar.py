import streamlit as st
from datetime import datetime, timedelta

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
    # 计算当月最后一天
    if month < 12:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, 12, 31)
    days_in_month = last_day.day  # 正确在函数内部定义
    first_weekday = first_day.weekday()  # 0=周一，6=周日

    # 事件数据映射
    date_events = {}
    if 'calendar_events' in st.session_state:
        for event in st.session_state.calendar_events:
            date_key = event["Date"].strftime("%Y-%m-%d")
            date_events[date_key] = event["Description"]

    # 星期标题
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # 绘制日历网格
    current_day = 1
    while current_day <= days_in_month:  # 这里正确引用函数内部的变量
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

                        # 卡片样式
                        day_classes = "calendar-day"
                        if is_today:
                            day_classes += " calendar-day-today"
                        if has_event:
                            day_classes += " calendar-day-has-event"

                        # 事件文本
                        event_text = f"<div class='event-text'>{date_events[date_key]}</div>" if has_event else ""

                        # 渲染卡片
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
                existing = next(
                    (e for e in st.session_state.calendar_events if e["Date"].date() == selected_date),
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
            if st.button("💾 SAVE EVENT", use_container_width=True, type="primary"):
                if not event_desc.strip():
                    st.error("Event description cannot be empty!")
                else:
                    if 'calendar_events' not in st.session_state:
                        st.session_state.calendar_events = []
                    # 更新事件
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"].date() != selected_date
                    ]
                    st.session_state.calendar_events.append({
                        "Date": selected_date,
                        "Description": event_desc.strip()
                    })
                    st.success("✅ Event saved successfully!")
        
        with col_delete:
            if st.button("🗑️ DELETE EVENT", use_container_width=True):
                if 'calendar_events' in st.session_state:
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"].date() != selected_date
                    ]
                    st.success("✅ Event deleted successfully!")
