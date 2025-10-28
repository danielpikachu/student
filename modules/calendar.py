import streamlit as st
from datetime import datetime

def render_calendar():
    # 功能选项卡（标题统一为模块名风格）
    tab1, tab2 = st.tabs(["View Calendar", "Add New Event"])
    
    with tab1:
        st.subheader("Calendar Events")
        if st.session_state.calendar_events:
            # 按日期排序（使用标准化字段名 "Date"）
            sorted_events = sorted(
                st.session_state.calendar_events,
                key=lambda x: (x["Date"], x["Time"])
            )
            
            # 显示事件列表（字段与 Google Sheet 对应）
            for i, event in enumerate(sorted_events):
                cols = st.columns([2, 1, 1, 2, 1])
                cols[0].write(event["Title"])
                cols[1].write(event["Date"].strftime("%Y-%m-%d"))
                cols[2].write(event["Time"].strftime("%H:%M"))
                cols[3].write(event["Location"])
                if cols[4].button("Delete", key=f"cal_del_{i}"):
                    st.session_state.calendar_events.pop(i)
                    st.success("Event deleted")
                    st.experimental_rerun()
        else:
            st.info("No events yet. Add a new event.")
    
    with tab2:
        st.subheader("Add New Event")
        with st.form("new_calendar_event"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Title*")
                date = st.date_input("Date*", min_value=datetime.today())
                time = st.time_input("Time*")
            
            with col2:
                location = st.text_input("Location*")
                organizer = st.text_input("Organizer*")
                description = st.text_area("Description")
            
            submit = st.form_submit_button("Save Event")
            
            if submit:
                if not all([title, location, organizer]):
                    st.error("Fields marked with * are required")
                else:
                    # 新增事件（字段名与 Google Sheet 列名严格一致）
                    st.session_state.calendar_events.append({
                        "Title": title,
                        "Date": date,
                        "Time": time,
                        "Location": location,
                        "Organizer": organizer,
                        "Description": description
                    })
                    st.success("Event added successfully!")
