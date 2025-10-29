import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（核心：用列表存储操作指令，实时消费）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 交易主列表
    if "pending_actions" not in st.session_state:
        st.session_state.pending_actions = []  # 待执行操作（add/del），实时消费
    if "action_tip" not in st.session_state:
        st.session_state.action_tip = {"show": False, "type": "", "msg": ""}  # 操作提示

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 实时消费待执行操作（先执行操作，再渲染界面，无延迟）--------------------------
    # 遍历待执行操作，逐个执行（新增/删除）
    for action in st.session_state.pending_actions.copy():  # 用copy避免遍历中修改列表
        if action["type"] == "add":
            # 执行新增：直接添加到交易列表
            st.session_state.money_transfers.append(action["data"])
            st.session_state.action_tip = {"show": True, "type": "success", "msg": "Transaction recorded successfully!"}
        elif action["type"] == "del":
            # 执行删除：根据UUID精准移除
            st.session_state.money_transfers = [t for t in st.session_state.money_transfers if t["uuid"] != action["uuid"]]
            st.session_state.action_tip = {"show": True, "type": "success", "msg": "Transaction deleted successfully!"}
        # 执行后从待执行列表中移除，避免重复执行
        st.session_state.pending_actions.remove(action)

    # -------------------------- 3. 显示操作提示（单次点击后实时显示）--------------------------
    if st.session_state.action_tip["show"]:
        if st.session_state.action_tip["type"] == "success":
            st.success(st.session_state.action_tip["msg"])
        else:
            st.error(st.session_state.action_tip["msg"])
        # 重置提示状态，避免重复显示
        st.session_state.action_tip["show"] = False

    # -------------------------- 4. 交易记录表格（纯Markdown，无刷新，单次点击删除）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 表头：严格按需求顺序（No.→Date→Amount→Description→Handled By→Transaction Type）
        header = ["No.", "Date", "Amount", "Description", "Handled By", "Transaction Type"]
        st.markdown(f"| {' | '.join(header)} |", unsafe_allow_html=True)
        st.markdown("|" + "---|" * len(header), unsafe_allow_html=True)

        # 渲染数据行+删除按钮（key=UUID，每个交易唯一，无重复）
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

            # 删除按钮：单次点击→添加删除指令到pending_actions
            btn_key = f"del_{trans['uuid']}"  # UUID唯一，无重复key错误
            if st.button(f"Delete #{seq}", key=btn_key, type="primary"):
                # 不执行删除，仅添加操作指令到列表（后续实时消费）
                st.session_state.pending_actions.append({"type": "del", "uuid": trans["uuid"]})
                # 强制组件重新渲染（通过空状态更新触发，无rerun）
                st.session_state.action_tip = st.session_state.action_tip

    st.write("=" * 50)

    # -------------------------- 5. 新增交易表单（单次点击→添加新增指令，无刷新）--------------------------
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

        # 提交按钮：单次点击→添加新增指令到pending_actions
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)
        if submit_btn:
            # 校验必填字段
            if not (amount and desc and handler):
                st.session_state.action_tip = {"show": True, "type": "error", "msg": "Required fields: Amount, Description, Handled By!"}
            else:
                # 构造交易数据，添加到待执行列表（不立即执行，后续实时消费）
                new_trans = {
                    "uuid": str(uuid.uuid4()),  # 唯一标识，避免删除错误
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                }
                st.session_state.pending_actions.append({"type": "add", "data": new_trans})
                # 强制组件重新渲染（通过空状态更新触发）
                st.session_state.action_tip = st.session_state.action_tip
