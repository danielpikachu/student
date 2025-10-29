import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（核心：用原子状态避免操作冲突）--------------------------
    # 原子状态：确保每个操作仅执行一次，无延迟/错乱
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 交易主列表
    if "delete_uuid" not in st.session_state:
        st.session_state.delete_uuid = None  # 待删除交易的UUID（原子状态，非列表）
    if "new_trans_data" not in st.session_state:
        st.session_state.new_trans_data = None  # 待新增的交易数据（原子状态，非列表）
    if "error_msg" not in st.session_state:
        st.session_state.error_msg = None  # 错误提示（原子状态）
    if "success_msg" not in st.session_state:
        st.session_state.success_msg = None  # 成功提示（原子状态）

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 原子化执行操作（先执行、再清空状态，确保单次生效）--------------------------
    # ① 执行新增：检测到new_trans_data立即执行（原子操作，仅一次）
    if st.session_state.new_trans_data is not None:
        st.session_state.money_transfers.append(st.session_state.new_trans_data)
        st.session_state.success_msg = "Transaction recorded successfully!"
        st.session_state.new_trans_data = None  # 立即清空状态，避免重复新增

    # ② 执行删除：检测到delete_uuid立即执行（原子操作，仅一次）
    if st.session_state.delete_uuid is not None:
        # 精准删除：仅移除匹配UUID的交易
        st.session_state.money_transfers = [
            trans for trans in st.session_state.money_transfers
            if trans["uuid"] != st.session_state.delete_uuid
        ]
        st.session_state.success_msg = "Transaction deleted successfully!"
        st.session_state.delete_uuid = None  # 立即清空状态，避免重复删除

    # -------------------------- 3. 显示提示信息（单次操作仅显示一次）--------------------------
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None  # 清空提示，避免重复显示
    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)
        st.session_state.error_msg = None  # 清空提示，避免重复显示

    # -------------------------- 4. 交易记录表格（Markdown+单次点击删除）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 表头：严格按需求顺序（No.→Date→Amount→Description→Handled By→Transaction Type）
        header = ["No.", "Date", "Amount", "Description", "Handled By", "Transaction Type"]
        st.markdown(f"| {' | '.join(header)} |", unsafe_allow_html=True)
        st.markdown("|" + "---|" * len(header), unsafe_allow_html=True)

        # 渲染数据行+删除按钮（UUID唯一key，无重复）
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx + 1
            date_str = trans["Date"].strftime("%Y/%m/%d")
            # 金额颜色：Income绿/Expense红（Markdown+HTML）
            amount_html = f"**<span style='color:green'>¥{trans['Amount']:.2f}</span>**" if trans["Type"] == "Income" else f"**<span style='color:red'>¥{trans['Amount']:.2f}</span>**"

            # 渲染表格行
            st.markdown(
                f"| {seq} | {date_str} | {amount_html} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |",
                unsafe_allow_html=True
            )

            # 删除按钮：单次点击→直接赋值delete_uuid（原子状态，无列表延迟）
            btn_key = f"del_{trans['uuid']}"  # UUID唯一，绝对不重复
            if st.button(f"Delete #{seq}", key=btn_key, type="primary"):
                # 直接赋值原子状态，函数开头立即执行删除
                st.session_state.delete_uuid = trans["uuid"]
                # 强制组件实时更新（通过空状态赋值触发，无刷新）
                st.session_state.success_msg = st.session_state.success_msg

    st.write("=" * 50)

    # -------------------------- 5. 新增交易表单（单次点击→直接赋值new_trans_data）--------------------------
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

        # 提交按钮：单次点击→直接赋值new_trans_data（原子状态）
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)
        if submit_btn:
            # 实时校验必填字段（不通过则显示错误，不进入待执行）
            if not (amount and desc and handler):
                st.session_state.error_msg = "Required fields: Amount, Description, Handled By!"
            else:
                # 直接构造交易数据并赋值原子状态，函数开头立即执行新增
                st.session_state.new_trans_data = {
                    "uuid": str(uuid.uuid4()),  # 唯一标识，避免删除错乱
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                }
                # 强制组件实时更新
                st.session_state.success_msg = st.session_state.success_msg
