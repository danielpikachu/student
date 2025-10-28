import streamlit as st
from datetime import datetime

def render_calendar():
    st.header("Calendar Management")
    st.write("Manage all student council events, meetings, and schedules here.")
    st.divider()  # 分隔线
    
    # 子选项卡：查看/添加日程
    view_tab, add_tab = st.tabs(["View Events", "Add New Event"])
    
    with view_tab:
        st.subheader("Upcoming Events")
        if st.session_state.calendar_events:
            # 按日期排序
            sorted_events = sorted(
                st.session_state.calendar_events,
                key=lambda x: (x["Date"], x["Time"])
            )
            
            # 用卡片式布局展示日程
            for i, event in enumerate(sorted_events):
                with st.card():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(event["Title"])
                        st.write(f"📅 {event['Date'].strftime('%Y-%m-%d')} | ⏰ {event['Time'].strftime('%H:%M')}")
                        st.write(f"📍 {event['Location']} | 👤 {event['Organizer']}")
                        if event["Description"]:
                            st.caption(f"Description: {event['Description']}")
                    with col2:
                        st.write("")  # 留白
                        st.write("")
                        if st.button("Delete", key=f"cal_del_{i}"):
                            st.session_state.calendar_events.pop(i)
                            st.success("Event deleted successfully!")
                            st.experimental_rerun()
        else:
            st.info("No events scheduled yet. Add a new event using the tab above.")
    
    with add_tab:
        st.subheader("Create New Event")
        with st.form("new_event_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Event Title *")
                date = st.date_input("Event Date *", min_value=datetime.today())
                time = st.time_input("Event Time *")
            
            with col2:
                location = st.text_input("Location *")
                organizer = st.text_input("Organizer *")
                description = st.text_area("Description (Optional)")
            
            submit = st.form_submit_button("Save Event", use_container_width=True)
            
            if submit:
                if not all([title, location, organizer]):
                    st.error("Fields marked with * are required!")
                else:
                    st.session_state.calendar_events.append({
                        "Title": title,
                        "Date": date,
                        "Time": time,
                        "Location": location,
                        "Organizer": organizer,
                        "Description": description
                    })
                    st.success(f"Event '{title}' added successfully!")
