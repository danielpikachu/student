import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

def render_calendar():
    st.header("Event Calendar")
    st.divider()

    # --------------------------
    # 顶部：原生月视图日历
    # --------------------------
    st.subheader("Monthly Calendar View")
    
    # 月份切换控制
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.today().replace(day=1)  # 当月第一天
    
    # 切换上月/下月
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("← Previous", use_container_width=True):
            prev_month = st.session_state.current_month.month - 1
            prev_year = st.session_state.current_month.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            st.session_state.current_month = datetime(prev_year, prev_month, 1)
    
    with col_title:
        st.markdown(f"### {st.session_state.current_month.strftime('%B %Y')}")
    
    with col_next:
        if st.button("Next →", use_container_width=True):
            next_month = st.session_state.current_month.month + 1
            next_year = st.session_state.current_month.year
            if next_month == 13:
                next_month = 1
                next_year += 1
            st.session_state.current_month = datetime(next_year, next_month, 1)

    # 生成当月日历数据
    year, month = st.session_state.current_month.year, st.session_state.current_month.month
    first_day = datetime(year, month, 1)
    last_day = (datetime(year, month+1, 1) - timedelta(days=1)) if month < 12 else datetime(year, 12, 31)
    days_in_month = last_day.day

    # 获取当月第一天是星期几（0=周一，6=周日）
    first_weekday = first_day.weekday()

    # 存储日历数据（日期 -> 事件）
    date_events = {}
    if 'calendar_events' in st.session_state:
        for event in st.session_state.calendar_events:
            date_str = event["Date"].strftime("%Y-%m-%d")
            date_events[date_str] = event["Description"]

    # 绘制日历网格
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    st.write(" | ".join([f"**{d}**" for d in weekdays]))  # 星期标题
    st.write("---")

    # 填充日历单元格
    current_day = 1
    calendar_rows = []
    while current_day <= days_in_month:
        row = []
        for weekday in range(7):
            if current_day == 1 and weekday < first_weekday:
                # 月初空白单元格
                row.append(" ")
            else:
                if current_day > days_in_month:
                    # 月末空白单元格
                    row.append(" ")
                else:
                    # 填充日期和事件
                    date_str = f"{year}-{month:02d}-{current_day:02d}"
                    day_label = f"{current_day}"
                    
                    # 标记当天和有事件的日期
                    is_today = (datetime.today().date() == datetime(year, month, current_day).date())
                    has_event = date_str in date_events
                    
                    # 样式处理
                    if is_today:
                        day_label = f"**🔴 {day_label}**"  # 今天标红
                    elif has_event:
                        day_label = f"**🔵 {day_label}**"  # 有事件标蓝
                    
                    row.append(day_label)
                    current_day += 1
        calendar_rows.append(" | ".join(row))

    # 显示日历行
    for row in calendar_rows:
        st.write(row)
        st.write("---")

    # --------------------------
    # 底部：事件管理（Admin Only）
    # --------------------------
    with st.expander("Manage Calendar Events (Admin Only)"):
        st.subheader("Add/Edit Calendar Entry")
        
        # 选择日期
        selected_date = st.date_input(
            "Select Date",
            value=datetime.today()
        )
        
        # 事件描述（限制100字符）
        event_desc = st.text_area(
            "Event Description (max 100 characters)",
            max_chars=100,
            placeholder="Enter event details..."
        )
        
        # 加载选中日期的已有事件
        if 'calendar_events' in st.session_state:
            existing_event = next(
                (e for e in st.session_state.calendar_events 
                 if e["Date"].date() == selected_date),
                None
            )
            if existing_event and not event_desc:
                event_desc = existing_event["Description"]  # 自动填充已有事件
        
        # 保存/删除按钮
        col_save, col_delete = st.columns(2)
        with col_save:
            if st.button("SAVE EVENTS", use_container_width=True):
                if not event_desc.strip():
                    st.error("Event description cannot be empty!")
                else:
                    # 初始化事件列表
                    if 'calendar_events' not in st.session_state:
                        st.session_state.calendar_events = []
                    
                    # 更新或添加事件
                    event_data = {
                        "Date": selected_date,
                        "Description": event_desc.strip()
                    }
                    
                    # 移除旧事件（如果存在）
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"].date() != selected_date
                    ]
                    # 添加新事件
                    st.session_state.calendar_events.append(event_data)
                    st.success("Event saved successfully!")
        
        with col_delete:
            if st.button("DELETE EVENT", use_container_width=True):
                if 'calendar_events' in st.session_state:
                    # 删除选中日期的事件
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"].date() != selected_date
                    ]
                    st.success("Event deleted successfully!")
