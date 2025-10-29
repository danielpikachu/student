import streamlit as st
from datetime import datetime
import uuid
import time  # 用于生成时间戳，确保key绝对唯一

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（核心：确保所有状态首次运行已定义）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 存储所有交易记录
    if "del_triggered" not in st.session_state:
        st.session_state.del_triggered = False  # 删除触发标记（替代递归重调）
    if "del_uuid" not in st.session_state:
        st.session_state.del_uuid = ""  # 待删除交易的UUID（唯一标识）
    if "add_tip" not in st.session_state:
        st.session_state.add_tip = {"type": "", "msg": ""}  # 新增提示
    if "render_timestamp" not in st.session_state:
        st.session_state.render_timestamp = str(time.time_ns())  # 渲染时间戳，用于key唯一

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 处理删除操作（先执行删除，再渲染表格，避免key冲突）--------------------------
    if st.session_state.del_triggered and st.session_state.del_uuid:
        # 根据UUID找到并删除交易（唯一标识，精准无错）
        st.session_state.money_transfers = [
            t for t in st.session_state.money_transfers 
            if t["uuid"] != st.session_state.del_uuid
        ]
        st.success("Transaction deleted successfully!")
        # 重置删除状态，避免重复删除
        st.session_state.del_triggered = False
        st.session_state.del_uuid = ""
        # 刷新时间戳，确保下次渲染的按钮key完全不同
        st.session_state.render_timestamp = str(time.time_ns())

    # -------------------------- 3. 交易记录表格（纯Markdown，无DataFrame，key绝对唯一）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 步骤1：构建表格数据（纯列表，无任何依赖）
        # 表头顺序：No.（序列列）→ Date → Amount → Description → Handled By → Transaction Type
        table_header = ["No.", "Date", "Amount", "Description", "Handled By", "Transaction Type"]
        st.markdown("| " + " | ".join(table_header) + " |", unsafe_allow_html=True)
        st.markdown("|" + "---|" * len(table_header), unsafe_allow_html=True)  # 表头分隔线

        # 步骤2：渲染数据行+删除按钮（key=时间戳+UUID，绝对不重复）
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq_num = idx + 1  # 序列列
            date_str = trans["Date"].strftime("%Y/%m/%d")  # 日期
            # 金额颜色：Income绿、Expense红（Markdown+HTML）
            amount_html = f"**<span style='color:green'>¥{trans['Amount']:.2f}</span>**" if trans["Type"] == "Income" else f"**<span style='color:red'>¥{trans['Amount']:.2f}</span>**"
            
            # 渲染表格行
            st.markdown(
                f"| {seq_num} | {date_str} | {amount_html} | {trans['Description']} | {trans['Handler']} | {trans['Type']} |",
                unsafe_allow_html=True
            )

            # 生成唯一删除按钮key：时间戳（每次渲染不同）+ UUID（每个交易唯一）
            unique_btn_key = f"del_btn_{st.session_state.render_timestamp}_{trans['uuid']}"
            # 点击按钮→标记删除状态，不重调函数（避免key冲突）
            if st.button(
                f"Delete Transaction #{seq_num}", 
                key=unique_btn_key,
                type="primary"
            ):
                st.session_state.del_triggered = True
                st.session_state.del_uuid = trans["uuid"]
                # 强制刷新页面（用Streamlit原生刷新，而非函数重调）
                st.experimental_rerun()

        # 按钮区域分割线
        st.write("---")

    # 分割线：区分交易记录与新增区域
    st.write("=" * 50)

    # -------------------------- 4. 新增交易表单（提交后原生刷新，避免key冲突）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form", clear_on_submit=False):  # 关闭自动清空，避免状态混乱
        # 两列布局，优化视觉
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("Transaction Date", value=datetime.today())
            amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
            trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
        with col2:
            description = st.text_input("Description", value="Fundraiser proceeds").strip()
            handler = st.text_input("Handled By", value="Pikachu Da Best").strip()

        # 提交按钮
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)

        # 表单提交逻辑：新增后原生刷新，确保key唯一
        if submit_btn:
            if not (amount and description and handler):
                st.session_state.add_tip = {"type": "error", "msg": "Required fields: Amount, Description, Handled By!"}
            else:
                # 新增交易（带唯一UUID）
                st.session_state.money_transfers.append({
                    "uuid": str(uuid.uuid4()),  # 交易唯一标识
                    "Date": trans_date,
                    "Amount": round(amount, 2),
                    "Description": description,
                    "Handler": handler,
                    "Type": trans_type
                })
                st.session_state.add_tip = {"type": "success", "msg": "Transaction recorded successfully! (Check the table above)"}
            # 原生刷新页面，避免函数重调导致的key冲突
            st.experimental_rerun()

    # 显示新增提示（重置状态，避免重复显示）
    if st.session_state.add_tip["type"] == "success":
        st.success(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}
    elif st.session_state.add_tip["type"] == "error":
        st.error(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}
