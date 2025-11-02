import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 处理删除操作 - 只删除最后一行
    if st.button("Delete Last Transaction", key="del_last", use_container_width=True):
        if st.session_state.money_transfers:
            st.session_state.money_transfers.pop()  # 删除最后一个元素
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    st.subheader("Transaction History")
        
    # 表格样式 - 确保边框完整闭合
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
        # 创建表格数据
        table_data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx
            date = trans["Date"].strftime("%Y-%m-%d")
            amount = f"${trans['Amount']:.2f}"
            amount_class = "income" if trans["Type"] == "Income" else "expense"
            
            # 构建行数据
            table_data.append({
                "No.": seq,
                "Date": date,
                "Amount ($)": f'<span class="{amount_class}" style="text-align: right;">{amount}</span>',
                "Category": "None",
                "Description": trans["Description"],
                "Handled By": trans["Handler"]
            })
        
        # 渲染表格（使用Markdown表格）
        # 表头
        st.markdown("""
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
        """, unsafe_allow_html=True)
        
        # 表格内容
        for row in table_data:
            st.markdown(f"""
            <tr>
                <td>{row['No.']}</td>
                <td>{row['Date']}</td>
                <td style="text-align: right;">{row['Amount ($)']}</td>
                <td>{row['Category']}</td>
                <td>{row['Description']}</td>
                <td>{row['Handled By']}</td>
            </tr>
            """, unsafe_allow_html=True)
        
        # 闭合表格
        st.markdown("""
            </tbody>
        </table>
        """, unsafe_allow_html=True)

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
            st.session_state.money_transfers.append({
                "uuid": str(uuid.uuid4()),
                "Date": trans_date,
                "Type": trans_type,
                "Amount": round(amount, 2),
                "Description": desc,
                "Handler": handler
            })
            st.success("Transaction recorded successfully!")
            st.rerun()

# 执行函数
render_money_transfers()
