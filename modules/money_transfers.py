import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    # 功能选项卡
    tab1, tab2, tab3 = st.tabs(["Transfer Records", "Financial Stats", "Add Transfer"])
    
    with tab1:
        st.subheader("Money Transfer Records")
        if st.session_state.money_transfers:
            # 筛选功能（使用标准化字段）
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime(2020, 1, 1))
            with col2:
                end_date = st.date_input("End Date", datetime.today())
            
            type_filter = st.selectbox("Transfer Type", ["All", "Income", "Expense"])
            
            # 筛选逻辑
            filtered = [
                t for t in st.session_state.money_transfers
                if start_date <= t["Date"] <= end_date
                and (type_filter == "All" or t["Type"] == type_filter)
            ]
            
            # 显示记录（字段与 Google Sheet 对应）
            for i, trans in enumerate(filtered):
                cols = st.columns([1, 1, 2, 1, 2, 1])
                cols[0].write(trans["Date"].strftime("%Y-%m-%d"))
                cols[1].write(trans["Type"])
                cols[2].write(f"¥ {trans['Amount']:.2f}")
                cols[3].write(trans["Group"] or "N/A")
                cols[4].write(trans["Description"])
                if cols[5].button("Delete", key=f"trans_del_{i}"):
                    st.session_state.money_transfers.remove(trans)
                    st.success("Transfer record deleted")
                    st.experimental_rerun()
        else:
            st.info("No transfer records yet. Add a new record.")
    
    with tab2:
        st.subheader("Financial Statistics")
        if st.session_state.money_transfers:
            # 计算收支（使用标准化字段 "Type" 和 "Amount"）
            total_income = sum(t["Amount"] for t in st.session_state.money_transfers 
                             if t["Type"] == "Income")
            total_expense = sum(t["Amount"] for t in st.session_state.money_transfers 
                              if t["Type"] == "Expense")
            balance = total_income - total_expense
            
            # 显示指标
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"¥ {total_income:.2f}")
            col2.metric("Total Expense", f"¥ {total_expense:.2f}")
            col3.metric("Current Balance", f"¥ {balance:.2f}")
            
            # 图表（数据结构适配 Google Sheet 导出）
            st.subheader("Income vs Expense")
            st.bar_chart(pd.DataFrame({
                "Category": ["Income", "Expense"],
                "Amount": [total_income, total_expense]
            }).set_index("Category"))
        else:
            st.info("No financial data. Add transfer records first.")
    
    with tab3:
        st.subheader("Add New Transfer")
        with st.form("new_transfer"):
            col1, col2 = st.columns(2)
            with col1:
                trans_type = st.radio("Transfer Type*", ["Income", "Expense"])
                amount = st.number_input("Amount (¥)*", min_value=0.01, step=0.01)
                date = st.date_input("Date*", datetime.today())
            
            with col2:
                group = st.text_input("Related Group (Optional)")
                handler = st.text_input("Handler*")
                description = st.text_area("Description*")
            
            submit = st.form_submit_button("Save Transfer")
            
            if submit:
                if not all([amount, handler, description]):
                    st.error("Fields marked with * are required")
                else:
                    # 新增交易记录（字段名与 Google Sheet 严格一致）
                    st.session_state.money_transfers.append({
                        "Date": date,
                        "Type": trans_type,
                        "Amount": amount,
                        "Group": group,
                        "Handler": handler,
                        "Description": description
                    })
                    st.success("Transfer record added!")
