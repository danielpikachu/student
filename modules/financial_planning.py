# modules/financial_planning.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render_financial_planning():
    st.subheader("💰 Financial Dashboard")
    st.markdown("---")

    # 1. 筹款目标与进度
    col1, col2 = st.columns(2)
    with col1:
        current_funds = st.number_input(
            "Current Funds Raised", 
            value=0.0, 
            step=10.0,
            format="%.2f",
            key="financial_current_funds"  # 添加唯一key
        )
    with col2:
        annual_target = st.number_input(
            "Annual Fundraising Target", 
            value=15000.0, 
            step=100.0,
            format="%.2f",
            key="financial_annual_target"  # 添加唯一key
        )
    progress_percent = (current_funds / annual_target) * 100 if annual_target > 0 else 0
    st.progress(progress_percent / 100)
    st.caption(f"Progress: {progress_percent:.1f}% of ${annual_target:.2f} target")

    # 2. 事件表格与管理
    if "scheduled_events" not in st.session_state:
        st.session_state.scheduled_events = []
    if "occasional_events" not in st.session_state:
        st.session_state.occasional_events = []

    # 定期事件
    st.subheader("Scheduled Events")
    df_scheduled = pd.DataFrame(st.session_state.scheduled_events, columns=["EventName", "Date", "Location", "Organizer"])
    st.dataframe(df_scheduled, use_container_width=True)
    with st.expander("Manage Scheduled Events (Admin Only)"):
        admin_pwd_sched = st.text_input(
            "Enter Admin Password", 
            type="password",
            key="financial_sched_pwd"  # 添加唯一key
        )
        if admin_pwd_sched == "sc_admin_2025":
            with st.form("scheduled_event_form", clear_on_submit=True):
                event_name = st.text_input("Event Name", key="sched_event_name")
                event_date = st.date_input("Event Date", value=datetime.now(), key="sched_event_date")
                event_location = st.text_input("Location", key="sched_event_loc")
                event_organizer = st.text_input("Organizer", key="sched_event_org")
                submit = st.form_submit_button("Add Event")
                if submit:
                    new_event = {
                        "EventName": event_name,
                        "Date": event_date.strftime("%Y-%m-%d"),
                        "Location": event_location,
                        "Organizer": event_organizer
                    }
                    st.session_state.scheduled_events.append(new_event)
                    st.success("Scheduled event added!")

    # 临时事件
    st.subheader("Occasional Events")
    df_occasional = pd.DataFrame(st.session_state.occasional_events, columns=["EventName", "Date", "Description", "Cost"])
    st.dataframe(df_occasional, use_container_width=True)
    with st.expander("Manage Occasional Events (Admin Only)"):
        admin_pwd_occ = st.text_input(
            "Enter Admin Password", 
            type="password",
            key="financial_occ_pwd"  # 添加唯一key
        )
        if admin_pwd_occ == "sc_admin_2025":
            with st.form("occasional_event_form", clear_on_submit=True):
                event_name_occ = st.text_input("Event Name", key="occ_event_name")
                event_date_occ = st.date_input("Event Date", value=datetime.now(), key="occ_event_date")
                event_desc = st.text_area("Description", key="occ_event_desc")
                event_cost = st.number_input("Cost ($)", value=0.0, step=10.0, format="%.2f", key="occ_event_cost")
                submit_occ = st.form_submit_button("Add Event")
                if submit_occ:
                    new_event_occ = {
                        "EventName": event_name_occ,
                        "Date": event_date_occ.strftime("%Y-%m-%d"),
                        "Description": event_desc,
                        "Cost": event_cost
                    }
                    st.session_state.occasional_events.append(new_event_occ)
                    st.success("Occasional event added!")

    # 3. 年度预计资金
    st.subheader("Annual Projected Funds")
    projected = current_funds + sum(e["Cost"] for e in st.session_state.occasional_events if e["Cost"] > 0)
    st.markdown(f"**${projected:.2f}**")
