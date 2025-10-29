# modules/financial_planning.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render_financial_planning():
    """渲染财务规划仪表盘界面（与示例UI完全对齐）"""
    st.subheader("💰 Financial Dashboard")
    st.markdown("---")

    # ========== 1. 筹款目标与进度 ==========
    col1, col2 = st.columns(2)
    with col1:
        current_funds = st.number_input(
            "Current Funds Raised", 
            value=0.0, 
            step=10.0,
            format="%.2f"
        )
    with col2:
        annual_target = st.number_input(
            "Annual Fundraising Target", 
            value=15000.0, 
            step=100.0,
            format="%.2f"
        )
    # 计算进度百分比
    progress_percent = (current_funds / annual_target) * 100 if annual_target > 0 else 0
    st.progress(progress_percent / 100)
    st.caption(f"Progress: {progress_percent:.1f}% of ${annual_target:.2f} target")

    # ========== 2. 事件表格与管理（分Scheduled和Occasional两类） ==========
    # 初始化会话状态数据
    if "scheduled_events" not in st.session_state:
        st.session_state.scheduled_events = []  # 存储定期事件：EventName, Date, Location, Organizer
    if "occasional_events" not in st.session_state:
        st.session_state.occasional_events = []  # 存储临时事件：EventName, Date, Description, Cost

    # ---- 定期事件（Scheduled Events） ----
    st.subheader("Scheduled Events")
    df_scheduled = pd.DataFrame(st.session_state.scheduled_events, columns=["EventName", "Date", "Location", "Organizer"])
    st.dataframe(df_scheduled, use_container_width=True)
    # 管理员折叠面板：添加/编辑定期事件
    with st.expander("Manage Scheduled Events (Admin Only)"):
        admin_pwd = st.text_input("Enter Admin Password", type="password")
        if admin_pwd == "sc_admin_2025":
            with st.form("scheduled_event_form"):
                event_name = st.text_input("Event Name")
                event_date = st.date_input("Event Date", value=datetime.now())
                event_location = st.text_input("Location")
                event_organizer = st.text_input("Organizer")
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

    # ---- 临时事件（Occasional Events） ----
    st.subheader("Occasional Events")
    df_occasional = pd.DataFrame(st.session_state.occasional_events, columns=["EventName", "Date", "Description", "Cost"])
    st.dataframe(df_occasional, use_container_width=True)
    # 管理员折叠面板：添加/编辑临时事件
    with st.expander("Manage Occasional Events (Admin Only)"):
        admin_pwd_occ = st.text_input("Enter Admin Password", type="password")
        if admin_pwd_occ == "sc_admin_2025":
            with st.form("occasional_event_form"):
                event_name_occ = st.text_input("Event Name")
                event_date_occ = st.date_input("Event Date", value=datetime.now())
                event_desc = st.text_area("Description")
                event_cost = st.number_input("Cost ($)", value=0.0, step=10.0, format="%.2f")
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

    # ========== 3. 年度预计资金（Annual Projected Funds） ==========
    # 计算逻辑：当前资金 + 所有事件收入（此处简化为当前资金展示）
    st.subheader("Annual Projected Funds")
    st.markdown(f"**${current_funds + sum(e['Cost'] for e in st.session_state.occasional_events if e['Cost'] > 0):.2f}**")
