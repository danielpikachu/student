import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    if "delete_uuid" not in st.session_state:
        st.session_state.delete_uuid = None

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 处理删除操作
    if st.session_state.delete_uuid:
        st.session_state.money_transfers = [
            t for t in st.session_state.money_transfers
            if t["uuid"] != st.session_state.delete_uuid
        ]
        st.session_state.delete_uuid = None
        st.success("Transaction deleted successfully!")

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
        text-align: right;
    }
    .expense {
        color: red;
        text-align: right;
    }
    .delete-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 0.9em;
        width: 100%;
    }
    .delete-btn:hover {
        background-color: #ff3333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 先处理所有删除按钮点击事件
        delete_uuids = []
        for trans in st.session_state.money_transfers:
            btn_key = f"del_{trans['uuid']}"
            if st.button("Delete", key=btn_key, use_container_width=True):
                delete_uuids.append(trans["uuid"])
        
        # 执行删除操作
        if delete_uuids:
            st.session_state.delete_uuid = delete_uuids[0]
            st.rerun()
        
        # 构建表格HTML
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
        
        # 添加表格行
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx
            date = trans["Date"].strftime("%Y-%m-%d")
            amount_class = "income" if trans["Type"] == "Income" else "expense"
            
            # 生成表格行，最后一列是删除按钮
            table_html += f"""
            <tr>
                <td>{seq}</td>
                <td>{date}</td>
                <td class="{amount_class}">${trans['Amount']:.2f}</td>
                <td>None</td>
                <td>{trans['Description']}</td>
                <td>{trans['Handler']}</td>
                <td><button class="delete-btn">Delete</button></td>
            </tr>
            """
        
        # 闭合表格标签
        table_html += """
            </tbody>
        </table>
        """
        
        # 渲染表格
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
            st.session_state.money_transfers.append({
                "uuid": str(uuid.uuid4()),
                "Date": trans_date,
                "Type": trans_type,
                "amount": round(amount, 2),  # 修正键名小写，避免后续错误
                "Description": desc,
                "Handler": handler
            })
            st.success("Transaction recorded successfully!")
            st.rerun()

# 执行函数
render_money_transfers()
