import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 仅初始化核心交易列表（无任何多余状态）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 唯一核心状态：存储所有交易

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 交易记录表格（直接遍历+点击即删）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 表头（固定顺序：No.→Date→Amount→Description→Handled By→Transaction Type）
        st.markdown("| No. | Date | Amount | Description | Handled By | Transaction Type |", unsafe_allow_html=True)
        st.markdown("|-----|------|--------|-------------|------------|------------------|", unsafe_allow_html=True)

        # 遍历交易：直接操作列表，点击删除按钮立即移除
        for idx in range(len(st.session_state.money_transfers)):
            trans = st.session_state.money_transfers[idx]
            seq = idx + 1
            date = trans["Date"].strftime("%Y/%m/%d")
            # 金额颜色（Income绿/Expense红）
            amount = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>" if trans["Type"] == "Income" else f"<span style='color:red'>¥{trans['Amount']:.2f}</span>"

            # 渲染表格行
            st.markdown(
                f"| {seq} | {date} | {amount} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |",
                unsafe_allow_html=True
            )

            # 删除按钮：点击即从列表中移除（无任何状态标记，直接操作）
            delete_key = f"del_{trans['uuid']}"
            if st.button(f"Delete #{seq}", key=delete_key, type="primary"):
                st.session_state.money_transfers.pop(idx)  # 立即删除当前索引的交易
                st.success(f"Transaction #{seq} deleted successfully!")
                # 强制页面重新渲染（仅用Streamlit原生表单刷新，无额外依赖）
                st.experimental_rerun()

    st.write("=" * 50)

    # -------------------------- 3. 新增交易表单（提交即加，无延迟）--------------------------
    st.subheader("Record New Transaction")
    # 用普通容器替代form，避免表单提交延迟（核心修复！）
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today())
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best").strip()

    # 新增按钮：普通按钮（非表单提交），点击即新增
    if st.button("Record Transaction", use_container_width=True, type="primary"):
        # 校验必填字段
        if not (amount and desc and handler):
            st.error("Required fields: Amount, Description, Handled By!")
        else:
            # 立即添加到交易列表
            st.session_state.money_transfers.append({
                "uuid": str(uuid.uuid4()),
                "Date": trans_date,
                "Type": trans_type,
                "Amount": round(amount, 2),
                "Description": desc,
                "Handler": handler
            })
            st.success("Transaction recorded successfully!")
            # 强制页面重新渲染，新增记录立即显示
            st.experimental_rerun()
