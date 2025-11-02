import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 处理删除操作
    if st.button("Delete Last Transaction", key="mt_del_last", use_container_width=True):
        if st.session_state.money_transfers:
            st.session_state.money_transfers.pop()
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    st.subheader("Transaction History")
        
    # 表格样式优化
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    .transaction-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    .column-names {
        background-color: #e8f4f8; /* 列名行背景色 */
        font-weight: 600;
    }
    .income { color: green; }
    .expense { color: red; }
    .amount-col { text-align: right !important; }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No transactions recorded yet")
    else:
        # 构建表格HTML
        table_html = """
        <table class="transaction-table">
            <tbody>
        """
        
        # 添加列名行（第一行固定为列名）
        table_html += """
            <tr class="column-names">
                <td>Date</td>
                <td class="amount-col">Amount ($)</td>
                <td>Category</td>
                <td>Description</td>
                <td>Handled By</td>
            </tr>
        """
        
        # 添加实际数据行（从第二行开始）
        for trans in st.session_state.money_transfers:
            table_html += f"""
            <tr>
                <td>{trans['Date'].strftime('%Y-%m-%d')}</td>
                <td class="amount-col { 'income' if trans['Type'] == 'Income' else 'expense' }">
                    ${trans['Amount']:.2f}
                </td>
                <td>None</td>
                <td>{trans['Description']}</td>
                <td>{trans['Handler']}</td>
            </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    # 新增交易区域（与表格列对应）
    st.subheader("Record New Transaction")
    cols = st.columns(5)  # 5列对应表格的5个字段
    with cols[0]:
        trans_date = st.date_input("Date", datetime.today(), key="mt_date")
    with cols[1]:
        amount = st.number_input("Amount ($)", 0.01, step=0.01, key="mt_amount")
    with cols[2]:
        trans_type = st.radio("Type", ["Income", "Expense"], key="mt_type", horizontal=True)
    with cols[3]:
        desc = st.text_input("Description", key="mt_desc").strip()
    with cols[4]:
        handler = st.text_input("Handled By", key="mt_handler").strip()

    if st.button("Record Transaction", key="mt_add", use_container_width=True, type="primary"):
        if not (amount and desc and handler):
            st.error("Please fill in all required fields!")
        else:
            st.session_state.money_transfers.append({
                "uuid": str(uuid.uuid4()),
                "Date": trans_date,
                "Type": trans_type,
                "Amount": round(amount, 2),
                "Description": desc,
                "Handler": handler
            })
            st.success("Transaction recorded!")
            st.rerun()

render_money_transfers()
