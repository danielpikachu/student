import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    if "action" not in st.session_state:
        st.session_state.action = None

    st.header("Financial Transactions")
    st.write("=" * 50)

    action_tip = None
    if st.session_state.action:
        if st.session_state.action["type"] == "add":
            st.session_state.money_transfers.append(st.session_state.action["data"])
            action_tip = "Transaction recorded successfully!"
        elif st.session_state.action["type"] == "del":
            st.session_state.money_transfers = [
                t for t in st.session_state.money_transfers
                if t["uuid"] != st.session_state.action["uuid"]
            ]
            action_tip = "Transaction deleted successfully!"
        st.session_state.action = None

    st.subheader("Transaction History")
    if action_tip:
        st.success(action_tip)
        
    # 匹配参考样式的表格CSS
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #e5e7eb;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #e5e7eb;
        padding: 8px 12px;
        text-align: left;
    }
    .transaction-table th {
        background-color: #f9fafb;
        font-weight: normal;
    }
    .income {
        color: green;
    }
    .expense {
        color: red;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        table_html = """
        <table class="transaction-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Date</th>
                    <th>Amount ($)</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Handled By</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx
            date = trans["Date"].strftime("%Y-%m-%d")
            amount_class = "income" if trans["Type"] == "Income" else "expense"
            del_key = f"del_{trans['uuid']}"
            
            table_html += f"""
            <tr>
                <td>{seq}</td>
                <td>{date}</td>
                <td class="{amount_class}" style="text-align: right;">${trans['Amount']:.2f}</td>
                <td>None</td>
                <td>{trans['Description']}</td>
                <td>{trans['Handler']}</td>
                <td>{st.button("Delete", key=del_key, type="primary", use_container_width=True)}</td>
            </tr>
            """
            
            if st.session_state.get(del_key, False):
                st.session_state.action = {"type": "del", "uuid": trans["uuid"]}
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
        
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="date_input_new")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, value=100.00, key="amount_input_new")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key="type_radio_new")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key="desc_input_new").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key="handler_input_new").strip()

    if st.button("Record Transaction", key="add_btn_new", use_container_width=True, type="primary"):
        if not (amount and desc and handler):
            st.error("Required fields: Amount, Description, Handled By!")
        else:
            st.session_state.action = {
                "type": "add",
                "data": {
                    "uuid": str(uuid.uuid4()),
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                }
            }
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
