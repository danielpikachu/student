import streamlit as st
import pandas as pd
from datetime import date

def render_money_transfers(is_admin):
    st.subheader("💸 Money Transfers")
    st.write("Record and view financial transactions")
    st.divider()
    
    # 显示交易记录
    st.subheader("Transaction History")
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False).reset_index(drop=True)
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "amount": st.column_config.NumberColumn("Amount ($)", format="$%.2f"),
                "desc": "Description",
                "handler": "Handled By"
            },
            hide_index=True
        )
        
        # 财务汇总
        income = sum(t["amount"] for t in st.session_state.transactions if t["amount"] > 0)
        expense = sum(t["amount"] for t in st.session_state.transactions if t["amount"] < 0)
        balance = income + expense
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"${income:.2f}")
        col2.metric("Total Expenses", f"${expense:.2f}")
        col3.metric("Current Balance", f"${balance:.2f}")
    else:
        st.info("No transactions recorded yet")
    
    # 管理员操作
    if is_admin:
        with st.expander("🔧 Record New Transaction (Admin Only)", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount ($)", value=100.0, step=10.0)
                is_expense = st.checkbox("Mark as Expense (negative amount)")
                if is_expense:
                    amount = -abs(amount)
            
            with col2:
                trans_date = st.date_input("Transaction Date", date.today())
                desc = st.text_input("Description", "e.g., Fundraiser, Supplies")
            
            handler = st.text_input("Handled By", st.session_state.user)
            
            if st.button("Record Transaction"):
                if not desc.strip():
                    st.error("Please enter a description")
                    return
                st.session_state.transactions.append({
                    "date": trans_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "desc": desc,
                    "handler": handler
                })
                st.success("Transaction recorded successfully")
