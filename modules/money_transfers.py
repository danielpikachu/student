import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 初始化核心状态（仅1份，无重复）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    if "action" not in st.session_state:
        st.session_state.action = None  # 格式：{"type": "add"/"del", "data"/"uuid": ...}

    # -------------------------- 2. 仅渲染1次完整界面框架（无重复区域）--------------------------
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 3. 执行操作（仅在当前渲染周期内，不触发重调）--------------------------
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

    # -------------------------- 4. Transaction History 区域（优化表格样式）--------------------------
    st.subheader("Transaction History")
    if action_tip:
        st.success(action_tip)
        
    # 自定义表格样式
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .transaction-table th, .transaction-table td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
    }
    .transaction-table th {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    .transaction-table tr:hover {
        background-color: #f9fafb;
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
        # 生成完整闭合的表格
        table_html = """
        <table class="transaction-table">
            <thead>
                <tr>
                    <th>No.</th>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Handled By</th>
                    <th>Transaction Type</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx + 1
            date = trans["Date"].strftime("%Y/%m/%d")
            amount_class = "income" if trans["Type"] == "Income" else "expense"
            
            # 为删除按钮生成唯一ID
            del_key = f"del_{trans['uuid']}"
            
            # 添加表格行
            table_html += f"""
            <tr>
                <td>{seq}</td>
                <td>{date}</td>
                <td class="{amount_class}">¥{trans['Amount']:.2f}</td>
                <td>{trans['Description']}</td>
                <td>{trans['Handler']}</td>
                <td>{trans['Type']}</td>
                <td>{st.button(f"Delete #{seq}", key=del_key, type="primary")}</td>
            </tr>
            """
            
            # 检查删除按钮点击事件
            if st.session_state.get(del_key, False):
                st.session_state.action = {"type": "del", "uuid": trans["uuid"]}
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
        
        # 闭合表格标签
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    # -------------------------- 5. Record New Transaction 区域--------------------------
    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="date_input")
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00, key="amount_input")
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
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
