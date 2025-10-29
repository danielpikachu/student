import streamlit as st
from datetime import datetime
import uuid
import time

def render_money_transfers():
    # -------------------------- 1. 仅初始化核心状态（无任何多余标记）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 唯一核心：交易列表
    if "component_id" not in st.session_state:
        st.session_state.component_id = str(uuid.uuid4())  # 动态组件ID，避免重复渲染

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 交易记录：实时遍历+点击即删（无刷新）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 表头（固定顺序）
        st.markdown("| No. | Date | Amount | Description | Handled By | Transaction Type |", unsafe_allow_html=True)
        st.markdown("|-----|------|--------|-------------|------------|------------------|", unsafe_allow_html=True)

        # 遍历交易：用动态ID确保组件每次渲染唯一
        current_id = st.session_state.component_id
        for idx in range(len(st.session_state.money_transfers)):
            trans = st.session_state.money_transfers[idx]
            seq = idx + 1
            date = trans["Date"].strftime("%Y/%m/%d")
            amount = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>" if trans["Type"] == "Income" else f"<span style='color:red'>¥{trans['Amount']:.2f}</span>"

            # 渲染表格行（用动态ID避免重复）
            st.markdown(
                f"<div id='row-{current_id}-{idx}'>| {seq} | {date} | {amount} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |</div>",
                unsafe_allow_html=True
            )

            # 删除按钮：点击即从列表移除（无任何刷新）
            delete_key = f"del-{current_id}-{trans['uuid']}"
            if st.button(f"Delete #{seq}", key=delete_key, type="primary"):
                st.session_state.money_transfers.pop(idx)  # 立即删除
                # 生成新组件ID，触发所有组件重新渲染（无rerun）
                st.session_state.component_id = str(uuid.uuid4())
                # 强制重新执行函数，显示删除后结果
                return render_money_transfers()

    st.write("=" * 50)

    # -------------------------- 3. 新增交易：点击即加（无表单延迟）--------------------------
    st.subheader("Record New Transaction")
    # 普通输入组件（无form，避免提交延迟）
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key=f"date-{st.session_state.component_id}")
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00, key=f"amount-{st.session_state.component_id}")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key=f"type-{st.session_state.component_id}")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key=f"desc-{st.session_state.component_id}").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key=f"handler-{st.session_state.component_id}").strip()

    # 新增按钮：点击即新增（无form提交延迟）
    add_key = f"add-{st.session_state.component_id}"
    if st.button("Record Transaction", key=add_key, use_container_width=True, type="primary"):
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
            # 生成新组件ID，触发重新渲染
            st.session_state.component_id = str(uuid.uuid4())
            # 强制重新执行函数，显示新增结果
            return render_money_transfers()
