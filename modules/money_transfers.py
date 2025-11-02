import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # 初始化状态
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    st.header("Transaction History")
    
    # 表格样式
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border: 1px solid #ccc;
        border-collapse: collapse;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #ccc;
        padding: 8px 12px;
    }
    .transaction-table th {
        background-color: #f0f0f0;
    }
    .income {
        color: green;
        text-align: right;
    }
    .expense {
        color: red;
        text-align: right;
    }
    .delete-btn {
        background: #ff4b4b;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    # 处理删除
    for i in range(len(st.session_state.transactions)):
        if st.button("Delete", key=f"del_{i}"):
            del st.session_state.transactions[i]
            st.experimental_rerun()

    # 显示表格
    if not st.session_state.transactions:
        st.info("No transactions yet")
    else:
        table = "<table class='transaction-table'><thead><tr>"
        table += "<th>No.</th><th>Date</th><th>Amount ($)</th><th>Category</th>"
        table += "<th>Description</th><th>Handled By</th><th>Action</th></tr></thead><tbody>"
        
        for idx, t in enumerate(st.session_state.transactions):
            table += f"<tr><td>{idx}</td>"
            table += f"<td>{t['date']}</td>"
            table += f"<td class='{t['class']}'>${t['amount']:.2f}</td>"
            table += f"<td>None</td>"
            table += f"<td>{t['desc']}</td>"
            table += f"<td>{t['handler']}</td>"
            table += f"<td><button class='delete-btn'>Delete</button></td></tr>"
        
        table += "</tbody></table>"
        st.markdown(table, unsafe_allow_html=True)

    # 添加新交易
    st.subheader("Add New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", datetime.today()).strftime("%Y-%m-%d")
        amount = st.number_input("Amount", 0.01, step=0.01)
        t_type = st.radio("Type", ["Income", "Expense"])
    with col2:
        desc = st.text_input("Description", "Fundraiser proceeds")
        handler = st.text_input("Handled By", "Pikachu Da Best")

    if st.button("Add Transaction"):
        st.session_state.transactions.append({
            "date": date,
            "amount": amount,
            "class": "income" if t_type == "Income" else "expense",
            "desc": desc,
            "handler": handler
        })
        st.success("Added successfully!")

if __name__ == "__main__":
    render_money_transfers()
