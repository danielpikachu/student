import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 初始化核心状态（仅1份，无重复）--------------------------
    # 唯一核心状态：交易列表（所有操作仅修改此列表，不重复生成界面）
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    # 操作标记：仅用于单次渲染周期内触发操作，避免重调导致区域重复
    if "action" not in st.session_state:
        st.session_state.action = None  # 格式：{"type": "add"/"del", "data"/"uuid": ...}

    # -------------------------- 2. 仅渲染1次完整界面框架（无重复区域）--------------------------
    # 页面标题（仅1次）
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 3. 执行操作（仅在当前渲染周期内，不触发重调）--------------------------
    action_tip = None  # 单次渲染内的提示，不存储到会话状态
    if st.session_state.action:
        if st.session_state.action["type"] == "add":
            # 执行新增：仅修改核心列表，不重调函数
            st.session_state.money_transfers.append(st.session_state.action["data"])
            action_tip = "Transaction recorded successfully!"
        elif st.session_state.action["type"] == "del":
            # 执行删除：仅修改核心列表，不重调函数
            st.session_state.money_transfers = [
                t for t in st.session_state.money_transfers
                if t["uuid"] != st.session_state.action["uuid"]
            ]
            action_tip = "Transaction deleted successfully!"
        # 清空操作标记：避免下次渲染重复执行
        st.session_state.action = None

    # -------------------------- 4. Transaction History 区域（仅1次渲染，原位置更新）--------------------------
    st.subheader("Transaction History")  # 仅1次显示，不重复
    if action_tip:
        st.success(action_tip)  # 操作提示仅在当前区域显示，不重复
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 表格仅1次渲染，数据随核心列表实时更新
        st.markdown("| No. | Date | Amount | Description | Handled By | Transaction Type |", unsafe_allow_html=True)
        st.markdown("|-----|------|--------|-------------|------------|------------------|", unsafe_allow_html=True)
        
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq = idx + 1
            date = trans["Date"].strftime("%Y/%m/%d")
            amount = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>" if trans["Type"] == "Income" else f"<span style='color:red'>¥{trans['Amount']:.2f}</span>"
            
            # 表格行仅1次渲染，数据实时更新
            st.markdown(
                f"| {seq} | {date} | {amount} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |",
                unsafe_allow_html=True
            )
            
            # 删除按钮：点击仅设置操作标记，不重调函数（避免区域重复）
            del_key = f"del_{trans['uuid']}"
            if st.button(f"Delete #{seq}", key=del_key, type="primary"):
                st.session_state.action = {"type": "del", "uuid": trans["uuid"]}
                # 强制当前组件重新渲染（无区域重复）
                st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()

    st.write("=" * 50)

    # -------------------------- 5. Record New Transaction 区域（仅1次渲染，原位置不变）--------------------------
    st.subheader("Record New Transaction")  # 仅1次显示，不重复
    # 输入组件仅1次渲染，不重复生成
    col1, col2 = st.columns(2)
    with col1:
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="date_input")
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00, key="amount_input")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key="type_radio")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key="desc_input").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key="handler_input").strip()

    # 新增按钮：点击仅设置操作标记，不重调函数（避免区域重复）
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
            # 强制当前组件重新渲染（无区域重复）
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
