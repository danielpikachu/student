import streamlit as st
from datetime import datetime
import pandas as pd
import streamlit_calendar as st_calendar  # 需先安装：pip install streamlit-calendar

def render_calendar():
    st.header("Event Calendar")
    st.divider()

    # --------------------------
    # 顶部：月视图日历（基于 streamlit-calendar 组件）
    # --------------------------
    st.subheader("Monthly Calendar View")
    
    # 初始化日历事件（从会话状态读取）
    events = []
    if 'calendar_events' in st.session_state:
        for idx, event in enumerate(st.session_state.calendar_events):
            events.append({
                "id": idx,
                "title": event["Description"],
                "start": event["Date"].isoformat(),
                "allDay": True
            })
    
    # 渲染 FullCalendar 组件
    selected_date = st_calendar.calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev",
                "center": "title",
                "right": "next"
            },
            "selectable": True,
            "height": 400
        },
        return_mode="single"
    )

    # --------------------------
    # 底部：管理员事件管理（折叠面板）
    # --------------------------
    with st.expander("Manage Calendar Events (Admin Only)"):
        st.subheader("Add/Edit Calendar Entry")
        
        # 日期选择（默认选中日历点击的日期）
        selected_date_input = st.date_input(
            "Select Date",
            value=pd.to_datetime(selected_date).date() if selected_date else datetime.today().date()
        )
        
        # 事件描述（限制100字符）
        event_desc = st.text_area(
            "Event Description (max 100 characters)",
            max_chars=100
        )
        
        # 按钮行
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Event"):
                if event_desc:
                    # 初始化会话状态的事件列表
                    if 'calendar_events' not in st.session_state:
                        st.session_state.calendar_events = []
                    
                    # 检查是否已有该日期的事件
                    existing_event = next(
                        (e for e in st.session_state.calendar_events 
                         if e["Date"].date() == selected_date_input),
                        None
                    )
                    
                    if existing_event:
                        # 更新已有事件
                        existing_event["Description"] = event_desc
                        st.success("Event updated successfully!")
                    else:
                        # 添加新事件
                        st.session_state.calendar_events.append({
                            "Date": datetime.combine(selected_date_input, datetime.min.time()),
                            "Description": event_desc
                        })
                        st.success("Event added successfully!")
                else:
                    st.error("Event description cannot be empty!")
        
        with col2:
            if st.button("Delete Event"):
                if 'calendar_events' in st.session_state:
                    # 过滤掉选中日期的事件
                    st.session_state.calendar_events = [
                        e for e in st.session_state.calendar_events 
                        if e["Date"].date() != selected_date_input
                    ]
                    st.success("Event deleted successfully!")
