# modules/financial_planning.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render_financial_planning():
    """渲染财务规划模块界面（fin_前缀命名空间）"""
    st.subheader("💰 Financial Dashboard")
    st.markdown("---")

    # ---------------------- 筹款目标与进度 ----------------------
    col1, col2 = st.columns(2)
    
    with col1:
        current_funds = st.number_input(
            "Current Funds Raised ($)", 
            value=st.session_state.fin_current_funds, 
            step=10.0,
            format="%.2f",
            key="fin_input_current_funds"  # 层级化Key：fin_模块_输入组件_当前资金
        )
        # 更新会话状态
        st.session_state.fin_current_funds = current_funds
    
    with col2:
        annual_target = st.number_input(
            "Annual Fundraising Target ($)", 
            value=st.session_state.fin_annual_target, 
            step=100.0,
            format="%.2f",
            key="fin_input_annual_target"  # 层级化Key：fin_模块_输入组件_年度目标
        )
        # 更新会话状态
        st.session_state.fin_annual_target = annual_target

    # 计算进度
    progress_percent = (current_funds / annual_target) * 100 if annual_target > 0 else 0
    st.progress(progress_percent / 100)
    st.caption(f"Progress: {progress_percent:.1f}% of ${annual_target:.2f} target")

    # ---------------------- 定期事件管理 ----------------------
    st.subheader("Scheduled Events")
    # 展示定期事件表格
    df_scheduled = pd.DataFrame(
        st.session_state.fin_scheduled_events,
        columns=["EventName", "Date", "Location", "Organizer"]
    )
    st.dataframe(df_scheduled, use_container_width=True)

    # 管理员操作：添加定期事件
    with st.expander("Manage Scheduled Events (Admin Only)"):
        admin_password = st.text_input(
            "Enter Admin Password", 
            type="password",
            key="fin_input_sched_admin_pwd"  # 层级化Key：fin_模块_输入组件_定期事件密码
        )
        
        if admin_password == st.session_state.sys_admin_password:
            with st.form("fin_form_scheduled_event", clear_on_submit=True):
                event_name = st.text_input("Event Name", key="fin_input_sched_name")
                event_date = st.date_input("Event Date", value=datetime.now(), key="fin_input_sched_date")
                event_location = st.text_input("Location", key="fin_input_sched_loc")
                event_organizer = st.text_input("Organizer", key="fin_input_sched_org")
                submit_btn = st.form_submit_button("Add Scheduled Event", key="fin_btn_sched_submit")
                
                if submit_btn:
                    if all([event_name.strip(), event_location.strip(), event_organizer.strip()]):
                        new_event = {
                            "EventName": event_name.strip(),
                            "Date": event_date.strftime("%Y-%m-%d"),
                            "Location": event_location.strip(),
                            "Organizer": event_organizer.strip()
                        }
                        st.session_state.fin_scheduled_events.append(new_event)
                        st.success("Scheduled event added successfully!")
                    else:
                        st.error("All fields (Event Name, Location, Organizer) are required!")

    # ---------------------- 临时事件管理 ----------------------
    st.subheader("Occasional Events")
    # 展示临时事件表格
    df_occasional = pd.DataFrame(
        st.session_state.fin_occasional_events,
        columns=["EventName", "Date", "Description", "Cost"]
    )
    st.dataframe(df_occasional, use_container_width=True)

    # 管理员操作：添加临时事件
    with st.expander("Manage Occasional Events (Admin Only)"):
        admin_password = st.text_input(
            "Enter Admin Password", 
            type="password",
            key="fin_input_occ_admin_pwd"  # 层级化Key：fin_模块_输入组件_临时事件密码
        )
        
        if admin_password == st.session_state.sys_admin_password:
            with st.form("fin_form_occasional_event", clear_on_submit=True):
                event_name = st.text_input("Event Name", key="fin_input_occ_name")
                event_date = st.date_input("Event Date", value=datetime.now(), key="fin_input_occ_date")
                event_desc = st.text_area("Description", key="fin_input_occ_desc")
                event_cost = st.number_input("Cost ($)", value=0.0, step=10.0, format="%.2f", key="fin_input_occ_cost")
                submit_btn = st.form_submit_button("Add Occasional Event", key="fin_btn_occ_submit")
                
                if submit_btn:
                    if event_name.strip() and event_desc.strip():
                        new_event = {
                            "EventName": event_name.strip(),
                            "Date": event_date.strftime("%Y-%m-%d"),
                            "Description": event_desc.strip(),
                            "Cost": round(event_cost, 2)
                        }
                        st.session_state.fin_occasional_events.append(new_event)
                        st.success("Occasional event added successfully!")
                    else:
                        st.error("Event Name and Description are required!")

    # ---------------------- 年度预计资金 ----------------------
    st.subheader("Annual Projected Funds")
    # 计算预计资金（当前资金 + 所有正向成本事件）
    positive_costs = sum(e["Cost"] for e in st.session_state.fin_occasional_events if e["Cost"] > 0)
    projected_funds = current_funds + positive_costs
    st.markdown(f"**Total Projected Funds: ${projected_funds:.2f}**")
    st.caption(f"Calculation: Current Funds (${current_funds:.2f}) + Positive Occasional Event Costs (${positive_costs:.2f})")
