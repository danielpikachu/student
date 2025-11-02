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
        
    # 优化表格样式 - 确保列对齐
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #ccc;
        margin: 1rem 0;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #ccc;
        padding: 8px 12px;
    }
    /* 第一列：序号 */
    .transaction-table th:nth-child(1),
    .transaction-table td:nth-child(1) {
        width: 5%;
        text-align: center;
    }
    /* 第二列：日期 */
    .transaction-table th:nth-child(2),
    .transaction-table td:nth-child(2) {
        width: 15%;
        text-align: left;
    }
    /* 第三列：金额 */
    .transaction-table th:nth-child(3),
    .transaction-table td:nth-child(3) {
        width: 15%;
        text-align: right;
    }
    /* 第四列：类别 */
    .transaction-table th:nth-child(4),
    .transaction-table td:nth-child(4) {
        width: 10%;
        text-align: left;
    }
    /* 第五列：描述 */
    .transaction-table th:nth-child(5),
    .transaction-table td:nth-child(5) {
        width: 30%;
        text-align: left;
    }
    /* 第六列：处理人 */
    .transaction-table th:nth-child(6),
    .transaction-table td:nth-child(6) {
        width: 25%;
        text-align: left;
    }
    .transaction-table th {
        background-color: #f0f0f0;
        font-weight: bold;
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
        # 构建表格（确保列顺序与表头完全一致）
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
                </tr>
            </thead>
            <tbody>
        """
        
        # 按顺序添加每一行数据（与表头列顺序严格对应）
        for idx, trans in enumerate(st.session_state.money_transfers, 1):  # 从1开始编号
            table_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{trans['Date'].strftime('%Y-%m-%d')}</td>
                <td class="{ 'income' if trans['Type'] == 'Income' else 'expense' }">
                    ${trans['Amount']:.2f}
                </td>
                <td>None</td>  <!-- 类别列 -->
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

    # 新增交易区域（与表格列宽比例一致）
    st.subheader("Record New Transaction")
    cols = st.columns([5, 15, 15, 10, 30, 25])  # 与表格列宽百分比严格对应
    with cols[0]:
        st.text("No. (Auto)")
    with cols[1]:
        trans_date = st.date_input("Date", datetime.today(), key="mt_date")
    with cols[2]:
        amount = st.number_input("Amount", 0.01, step=0.01, key="mt_amount")
    with cols[3]:
        trans_type = st.radio("Type", ["Income", "Expense"], key="mt_type", horizontal=True)
    with cols[4]:
        desc = st.text_input("Description", key="mt_desc").strip()
    with cols[5]:
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
