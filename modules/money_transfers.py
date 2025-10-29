import streamlit as st
from datetime import datetime
import uuid
import time

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保所有状态实时可用）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 交易记录列表
    if "add_data" not in st.session_state:
        st.session_state.add_data = None  # 存储单次新增的交易数据（点击即存）
    if "del_uuid" not in st.session_state:
        st.session_state.del_uuid = None  # 存储单次删除的交易UUID（点击即存）
    if "btn_timestamp" not in st.session_state:
        st.session_state.btn_timestamp = str(time.time_ns())  # 按钮key唯一标识

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 实时执行新增/删除操作（点击后立即执行，无延迟）--------------------------
    # ① 执行新增：检测到add_data立即添加到列表
    if st.session_state.add_data:
        st.session_state.money_transfers.append(st.session_state.add_data)
        st.success("Transaction recorded successfully!")
        st.session_state.add_data = None  # 重置新增数据，避免重复添加
        st.session_state.btn_timestamp = str(time.time_ns())  # 刷新按钮key

    # ② 执行删除：检测到del_uuid立即从列表移除
    if st.session_state.del_uuid:
        st.session_state.money_transfers = [t for t in st.session_state.money_transfers if t["uuid"] != st.session_state.del_uuid]
        st.success("Transaction deleted successfully!")
        st.session_state.del_uuid = None  # 重置删除标识，避免重复删除
        st.session_state.btn_timestamp = str(time.time_ns())  # 刷新按钮key

    # -------------------------- 3. 交易记录表格（Markdown+单次点击删除）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 表头：严格按需求顺序（No.→Date→Amount→Description→Handled By→Transaction Type）
        header = ["No.", "Date", "Amount", "Description", "Handled By", "Transaction Type"]
        st.markdown(f"| {' | '.join(header)} |", unsafe_allow_html=True)
        st.markdown("|" + "---|" * len(header), unsafe_allow_html=True)

        # 渲染数据行+删除按钮（单次点击即赋值del_uuid）
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx + 1
            date = trans["Date"].strftime("%Y/%m/%d")
            # 金额颜色：Income绿/Expense红
            amount = f"**<span style='color:green'>¥{trans['Amount']:.2f}</span>**" if trans["Type"] == "Income" else f"**<span style='color:red'>¥{trans['Amount']:.2f}</span>**"

            # 渲染表格行
            st.markdown(
                f"| {seq} | {date} | {amount} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |",
                unsafe_allow_html=True
            )

            # 唯一删除按钮key：时间戳+UUID（绝对不重复）
            btn_key = f"del_{st.session_state.btn_timestamp}_{trans['uuid']}"
            # 单次点击：直接赋值del_uuid（触发上方删除逻辑）
            if st.button(f"Delete #{seq}", key=btn_key, type="primary"):
                st.session_state.del_uuid = trans["uuid"]
                # 强制立即重渲染（无需等待二次点击）
                st.experimental_rerun()

        st.write("---")

    # 分割线：区分表格与表单
    st.write("=" * 50)

    # -------------------------- 4. 新增交易表单（单次点击即提交）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form", clear_on_submit=True):
        # 两列布局优化体验
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("Transaction Date", value=datetime.today())
            amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
            trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
        with col2:
            desc = st.text_input("Description", value="Fundraiser proceeds").strip()
            handler = st.text_input("Handled By", value="Pikachu Da Best").strip()

        # 提交按钮：单次点击即赋值add_data
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)
        if submit_btn:
            # 校验必填字段（实时提示错误）
            if not (amount and desc and handler):
                st.error("Required fields: Amount, Description, Handled By!")
            else:
                # 单次点击：直接构造交易数据并赋值add_data（触发上方新增逻辑）
                st.session_state.add_data = {
                    "uuid": str(uuid.uuid4()),
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                }
                # 强制立即重渲染（新增记录实时显示）
                st.experimental_rerun()
