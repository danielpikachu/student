import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    st.header("Money Transfers Management")
    st.write("Track all financial transactions, income, and expenses of the student council here.")
    st.divider()
    
    # 子选项卡：交易记录/财务统计/添加交易
    records_tab, stats_tab, add_tab = st.tabs(["Transaction Records", "Financial Statistics", "Add New Transaction"])
    
    with records_tab:
        st.subheader("All Transactions")
        if st.session_state.money_transfers:
            # 筛选功能
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", datetime(2020, 1, 1))
            with col2:
                end_date = st.date_input("End Date", datetime.today())
            
            type_filter = st.selectbox("Filter by Type", ["All", "Income", "Expense"])
            
            # 应用筛选
            filtered_trans = [
                t for t in st.session_state.money_transfers
                if start_date <= t["Date"] <= end_date
                and (type_filter == "All" or t["Type"] == type_filter)
            ]
            
            if filtered_trans:
                for i, trans in enumerate(filtered_trans):
                    with st.card():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader(f"{trans['Type']}: ¥{trans['Amount']:.2f}")
                            st.write(f"📅 {trans['Date'].strftime('%Y-%m-%d')} | 👤 Handler: {trans['Handler']}")
                            if trans["Group"]:
                                st.write(f"🏛️ Related Group: {trans['Group']}")
                            st.caption(f"Description: {trans['Description']}")
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("Delete", key=f"trans_del_{i}"):
                            st.session_state.money_transfers.remove(trans)
                            st.success("Transaction deleted successfully!")
                            st.experimental_rerun()
            else:
                st.info("No transactions match your filter criteria.")
        else:
            st.info("No transactions recorded yet. Add a transaction using the 'Add New Transaction' tab.")
    
    with stats_tab:
        st.subheader("Financial Overview")
        if st.session_state.money_transfers:
            # 计算收支
            total_income = sum(t["Amount"] for t in st.session_state.money_transfers 
                             if t["Type"] == "Income")
            total_expense = sum(t["Amount"] for t in st.session_state.money_transfers 
                              if t["Type"] == "Expense")
            balance = total_income - total_expense
            
            # 关键指标卡片
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", f"¥{total_income:.2f}", delta="+" if total_income > 0 else "")
            with col2:
                st.metric("Total Expense", f"¥{total_expense:.2f}", delta="-" if total_expense > 0 else "")
            with col3:
                st.metric("Current Balance", f"¥{balance:.2f}", 
                          delta=f"{balance/total_income*100:.1f}%" if total_income > 0 else "")
            
            # 收支图表
            st.subheader("Income vs Expense Distribution")
            st.bar_chart(
                pd.DataFrame({
                    "Category": ["Income", "Expense"],
                    "Amount (¥)": [total_income, total_expense]
                }).set_index("Category"),
                use_container_width=True
            )
        else:
            st.info("No financial data available. Add transactions to view statistics.")
    
    with add_tab:
        st.subheader("Record New Transaction")
        with st.form("new_transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                trans_type = st.radio("Transaction Type *", ["Income", "Expense"])
                amount = st.number_input("Amount (¥) *", min_value=0.01, step=0.01)
                date = st.date_input("Transaction Date *", datetime.today())
            
            with col2:
                group = st.text_input("Related Group (Optional)")
                handler = st.text_input("Handler *")
                description = st.text_area("Transaction Description *")
            
            submit = st.form_submit_button("Save Transaction", use_container_width=True)
            
            if submit:
                if not all([amount, handler, description]):
                    st.error("Fields marked with * are required!")
                else:
                    st.session_state.money_transfers.append({
                        "Date": date,
                        "Type": trans_type,
                        "Amount": amount,
                        "Group": group,
                        "Handler": handler,
                        "Description": description
                    })
                    st.success("Transaction recorded successfully!")
