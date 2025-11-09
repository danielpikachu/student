# modules/calendar.py
import streamlit as st
from datetime import datetime, timedelta
import sys
import os

# Resolve root directory module import issue
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import Google Sheets utility class
from google_sheet_utils import GoogleSheetHandler

# Custom CSS styles
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
    """Render calendar module interface (cal_ prefix namespace)"""
    add_custom_css()
    st.header("📅 Event Calendar")
    st.divider()

    # Initialize Google Sheets connection
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
        st.error(f"Google Sheets initialization failed: {str(e)}")

    # Sync data from Google Sheets (using cal_events state)
    if calendar_sheet and sheet_handler:
        try:
            all_data = calendar_sheet.get_all_values()
            expected_headers = ["date", "event"]
            
            # Check headers
            if not all_data or all_data[0] != expected_headers:
                calendar_sheet.clear()
                calendar_sheet.append_row(expected_headers)
                records = []
            else:
                # Process data (skip header)
                records = [
                    {"date": row[0], "event": row[1]} 
                    for row in all_data[1:] 
                    if row[0] and row[1]  # Ensure date and event are not empty
                ]
            
            # Convert to datetime format and update session state
            st.session_state.cal_events = [
                {
                    "date": datetime.strptime(record["date"], "%Y-%m-%d").date(),
                    "description": record["event"]
                } 
                for record in records
            ]
        except Exception as e:
            st.warning(f"Data synchronization failed: {str(e)}")

    # ---------------------- Month Navigation ----------------------
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    
    with col_prev:
        if st.button("← Previous Month", use_container_width=True, type="secondary", key="cal_btn_prev_month"):
            # Calculate previous month
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
            # Calculate next month
            current = st.session_state.cal_current_month
            next_month = current.month + 1
            next_year = current.year
            if next_month == 13:
                next_month = 1
                next_year += 1
            st.session_state.cal_current_month = datetime(next_year, next_month, 1)

    # ---------------------- Calendar Grid Calculation ----------------------
    year, month = st.session_state.cal_current_month.year, st.session_state.cal_current_month.month
    first_day = datetime(year, month, 1)
    
    # Calculate last day of the month
    if month < 12:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, 12, 31)
    
    days_in_month = last_day.day
    first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday

    # Build date-event mapping
    date_event_map = {}
    for event in st.session_state.cal_events:
        date_key = event["date"].strftime("%Y-%m-%d")
        date_event_map[date_key] = event["description"]

    # ---------------------- Render Calendar Grid ----------------------
    # Render weekday headers
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_cols = st.columns(7)
    for i, day in enumerate(weekdays):
        with weekday_cols[i]:
            st.markdown(f"<div class='weekday-label'>{day}</div>", unsafe_allow_html=True)

    # Render date grid
    current_day = 1
    while current_day <= days_in_month:
        day_cols = st.columns(7)
        for col_idx in range(7):
            with day_cols[col_idx]:
                # Handle empty cells before first day of month
                if current_day == 1 and col_idx < first_weekday:
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                elif current_day > days_in_month:
                    # Handle empty cells after last day of month
                    st.markdown("<div class='calendar-day'></div>", unsafe_allow_html=True)
                else:
                    # Render valid date cell
                    current_date = datetime(year, month, current_day).date()
                    date_key = current_date.strftime("%Y-%m-%d")
                    is_today = (current_date == datetime.today().date())
                    has_event = date_key in date_event_map

                    # Build CSS classes
                    day_classes = "calendar-day"
                    if is_today:
                        day_classes += " calendar-day-today"
                    if has_event:
                        day_classes += " calendar-day-has-event"

                    # Build event text
                    event_text = f"<div class='event-text'>{date_event_map[date_key]}</div>" if has_event else ""

                    # Render cell
                    st.markdown(f"""
                    <div class='{day_classes}'>
                        <div class='day-number'>{current_day}</div>
                        {event_text}
                    </div>
                    """, unsafe_allow_html=True)

                    current_day += 1

    # ---------------------- Event Management Panel (Admin Only) ----------------------
    st.divider()
    # Show edit area only for admins
    if st.session_state.auth_is_admin:
        with st.container(border=True):
            st.subheader("📝 Manage Calendar Events")
            
            # Event edit area (removed password verification)
            col_date, col_desc = st.columns([1, 2])
            
            with col_date:
                selected_date = st.date_input(
                    "Select Date",
                    value=datetime.today(),
                    label_visibility="collapsed",
                    key="cal_input_event_date"
                )
            
            with col_desc:
                # Check if there's an existing event for the selected date
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
            
            # Action buttons
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("💾 Save Event", use_container_width=True, type="primary", key="cal_btn_save_event"):
                    if not event_desc.strip():
                        st.error("Event description cannot be empty!")
                        return
                    
                    # Delete old event with the same date
                    st.session_state.cal_events = [
                        e for e in st.session_state.cal_events 
                        if e["date"] != selected_date
                    ]
                    
                    # Add new event
                    new_event = {
                        "date": selected_date,
                        "description": event_desc.strip()
                    }
                    st.session_state.cal_events.append(new_event)
                    
                    # Sync to Google Sheets
                    if calendar_sheet and sheet_handler:
                        try:
                            # Delete old records
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(selected_date):
                                    calendar_sheet.delete_rows(i)
                            
                            # Add new record
                            calendar_sheet.append_row([str(selected_date), event_desc.strip()])
                            st.success("✅ Event saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Failed to sync to Google Sheets: {str(e)}")
            
            with col_delete:
                if st.button("🗑️ Delete Event", use_container_width=True, key="cal_btn_delete_event"):
                    if not existing_event:
                        st.warning("No event found for this date!")
                        return
                    
                    # Delete local event
                    st.session_state.cal_events = [
                        e for e in st.session_state.cal_events 
                        if e["date"] != selected_date
                    ]
                    
                    # Sync deletion to Google Sheets
                    if calendar_sheet and sheet_handler:
                        try:
                            all_rows = calendar_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == str(selected_date):
                                    calendar_sheet.delete_rows(i)
                            st.success("✅ Event deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Failed to delete from Google Sheets: {str(e)}")
