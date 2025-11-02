import streamlit as st
from datetime import datetime
import uuid
import pandas as pd
from io import StringIO

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 处理删除操作
    delete_key = st.session_state.get("delete_key", None)
    if delete_key:
        st.session_state.money_transfers = [
            t for t in st.session_state.money_transfers
            if f"del_{t['uuid']}" != delete_key
        ]
        st.session_state.delete_key = None
        st.success("Transaction deleted successfully!")

    st.subheader("Transaction History")
        
    # 表格样式
    st.markdown("""
    <style>
    .dataframe-container table {
        border-collapse: collapse;
        border: 1px solid #ccc;
        width: 100%;
    }
    .dataframe-container th, .dataframe-container td {
        border: 1px solid #ccc !important;
        padding: 8px 12px !important;
    }
    .dataframe-container th {
        background-color: #f0f0f0 !important;
        font-weight: bold !important;
    }
    .income {
        color: green !important;
        text-align: right !important;
    }
    .expense {
        color: red !important;
        text-align: right !important;
    }
    .delete-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 3px;
        cursor: pointer;
        font-size: 0.9em;
    }
    .delete-btn:hover {
        background-color: #ff3333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 准备表格数据
        data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 创建删除按钮（使用唯一key）
            btn_key = f"del_{trans['uuid']}"
            
            # 检查按钮点击
            if st.button("Delete", key=btn_key, use_container_width=True):
                st.session_state.delete_key = btn_key
                st.rerun()
                
            # 添加行数据
            data.append({
                "No.": idx,
                "Date": trans["Date"].strftime("%Y-%m-%d"),
                "Amount ($)": f"${trans['Amount']:.2f}",
                "Category": "None",
                "Description": trans["Description"],
                "Handled By": trans["Handler"],
                "Action": f"<button class='delete-btn'>Delete</button>"  # 表格中显示的按钮
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 设置样式函数
        def style_table(row):
            styles = ["" for _ in row]
            # 设置金额列样式
            if row["Amount ($)"].startswith('$'):
                amount = float(row["Amount ($)"][1:])
                styles[2] = "income" if any(t["Amount"] == amount and t["Type"] == "Income" 
                                          for t in st.session_state.money_transfers) else "expense"
            return styles
        
        # 渲染表格
        styled_df = df.style.apply(style_table, axis=1)
        # 转换为HTML并渲染
        html = styled_df.to_html(escape=False, index=False)
        st.markdown(f'<div class="dataframe-container">{html}</div>', unsafe_allow_html=True)

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

render_money_transfers()
