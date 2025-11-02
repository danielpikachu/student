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

    # 处理操作
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
        
    # 表格样式优化
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #d1d5db;
        margin: 1rem 0;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #d1d5db;
        padding: 10px 12px;
        text-align: left;
    }
    .transaction-table th {
        background-color: #f3f4f6;
        font-weight: 600;
    }
    .transaction-table tr:nth-child(even) {
        background-color: #f9fafb;
    }
    .income {
        color: #16a34a;
        font-weight: 500;
    }
    .expense {
        color: #dc2626;
        font-weight: 500;
    }
    .delete-btn {
        background-color: #ef4444;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 0.85rem;
    }
    .delete-btn:hover {
        background-color: #dc2626;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 构建完整表格
        table_html = """
        <table class="transaction-table">
            <thead>
                <tr>
                    <th>No.</th>
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
            seq = idx  # 从0开始编号
            date = trans["Date"].strftime("%Y-%m-%d")
            amount_class = "income" if trans["Type"] == "Income" else "expense"
            del_key = f"del_{trans['uuid']}"
            
            # 单独创建删除按钮（避免直接渲染到HTML中）
            delete_button = st.button(
                "Delete", 
                key=del_key, 
                use_container_width=True,
                help="Delete this transaction"
            )
            
            # 检查删除操作
            if delete_button:
                st.session_state.action = {"type": "del", "uuid": trans["uuid"]}
                st.rerun()
            
            # 添加表格行（使用HTML按钮样式保持一致性）
            table_html += f"""
            <tr>
                <td>{seq}</td>
                <td>{date}</td>
                <td class="{amount_class}" style="text-align: right;">${trans['Amount']:.2f}</td>
                <td>None</td>
                <td>{trans['Description']}</td>
                <td>{trans['Handler']}</td>
                <td style="text-align: center;">
                    <button class="delete-btn">{delete_button}</button>
                </td>
            </tr>
            """
        
        # 闭合表格标签
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    # 新增交易区域
    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="date_input")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, value=100.00, key="amount_input")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key="type_radio")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key="desc_input").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key="handler_input").strip()

    if st.button("Record Transaction", key="add_btn", use_container_width=True, type="primary"):
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
            st.rerun()

# 运行函数
render_money_transfers()
