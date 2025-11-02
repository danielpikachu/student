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
    }
    /* 序号列 */
    .transaction-table th:nth-child(1),
    .transaction-table td:nth-child(1) {
        width: 5%;
        text-align: center;
    }
    /* 数据列（共5列） */
    .transaction-table th:nth-child(n+2),
    .transaction-table td:nth-child(n+2) {
        width: 19%; /* (100%-5%)/5=19% */
    }
    .transaction-table th:nth-child(3),
    .transaction-table td:nth-child(3) {
        text-align: right; /* 金额列右对齐 */
    }
    .transaction-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    .column-header-row {
        background-color: #e8f4f8; /* 列名行背景色 */
        font-weight: bold;
    }
    .income { color: green; }
    .expense { color: red; }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No transactions recorded yet")
    else:
        # 构建表格HTML
        table_html = """
        <table class="transaction-table">
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Data</th> <!-- 总列标题 -->
                </tr>
            </thead>
            <tbody>
        """
        
        # 遍历所有交易记录
        for idx, trans in enumerate(st.session_state.money_transfers, 1):
            # 第一行：列名行（Date → Amount → Category → Description → Handled By）
            table_html += f"""
            <tr class="column-header-row">
                <td>{idx}</td>
                <td>
                    Date → Amount → Category → Description → Handled By
                </td>
            </tr>
            """
            
            # 第二行：实际数据行
            table_html += f"""
            <tr>
                <td></td> <!-- 序号列留空 -->
                <td>
                    {trans['Date'].strftime('%Y-%m-%d')} → 
                    <span class="{ 'income' if trans['Type'] == 'Income' else 'expense' }">
                        ${trans['Amount']:.2f}
                    </span> → 
                    None → 
                    {trans['Description']} → 
                    {trans['Handler']}
                </td>
            </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    # 新增交易区域
    st.subheader("Record New Transaction")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        trans_date = st.date_input("Date", datetime.today(), key="mt_date")
    with col2:
        amount = st.number_input("Amount ($)", 0.01, step=0.01, key="mt_amount")
    with col3:
        trans_type = st.radio("Type", ["Income", "Expense"], key="mt_type", horizontal=True)
    with col4:
        desc = st.text_input("Description", key="mt_desc").strip()
    with col5:
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
