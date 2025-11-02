import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 处理删除操作 - 删除最后一行
    if st.button("Delete Last Transaction", key="del_last_btn", use_container_width=True):
        if st.session_state.money_transfers:
            st.session_state.money_transfers.pop()
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    st.subheader("Transaction History")
        
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 整理表格数据
        table_data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            table_data.append({
                "": idx,  # 序号列
                "Date": trans["Date"].strftime("%Y-%m-%d"),
                "Amount ($)": trans["Amount"],
                "Category": "None",
                "Description": trans["Description"],
                "Handled By": trans["Handler"]
            })
        
        # 使用Streamlit原生dataframe渲染（自动实现你要的表格样式）
        st.dataframe(
            table_data,
            column_config={
                "": st.column_config.NumberColumn(label="", format="%d"),  # 序号列格式
                "Amount ($)": st.column_config.NumberColumn(format="$%.2f")  # 金额列格式
            },
            hide_index=True,
            use_container_width=True
        )

    st.write("=" * 50)

    # 新增交易区域
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
