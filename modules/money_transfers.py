import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    # 初始化交易列表（首次新增时必须存在）
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    # 初始化新增成功标记（解决首次新增无反应问题）
    if "add_success" not in st.session_state:
        st.session_state.add_success = False
    # 初始化删除标记（避免删除时渲染冲突）
    if "del_uuid" not in st.session_state:
        st.session_state.del_uuid = None

    # 页面标题（基础组件，全版本兼容）
    st.header("Financial Transactions")
    st.write("=" * 40)

    # -------------------------- 2. 交易记录（极简表格+删除按钮）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理表格数据（仅纯文本/HTML，无复杂配置）
        table_rows = []
        del_buttons = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 金额颜色：用HTML标签，后续通过escape=False渲染
            amount_html = f"<span style='color:red'>-¥{trans['Amount']:.2f}</span>" if trans["Type"] == "Expense" else f"<span style='color:green'>¥{trans['Amount']:.2f}</span>"
            
            # 表格行：仅保留核心字段
            table_rows.append([
                idx + 1,  # 序号
                trans["Date"].strftime("%Y/%m/%d"),  # 日期
                amount_html,  # 金额（带颜色）
                trans["Description"],  # 描述
                trans["Handler"]  # 处理人
            ])
            
            # 生成唯一删除按钮（key含UUID，绝对不重复）
            btn_key = f"del_{trans['uuid']}"
            del_buttons.append(st.button(f"Delete #{idx+1}", key=btn_key))

        # 步骤2：渲染表格（移除所有可选参数，仅保留必选）
        # 关键：仅用DataFrame和index=False/escape=False，兼容所有版本
        st.dataframe(
            pd.DataFrame(
                table_rows,
                columns=["No.", "Date", "Amount", "Description", "Handled By"]  # 列名直接传入
            ),
            index=False,  # 隐藏默认索引
            escape=False  # 允许解析HTML颜色
        )

        # 步骤3：处理删除逻辑（点击按钮后标记待删除UUID）
        for idx, btn in enumerate(del_buttons):
            if btn:
                st.session_state.del_uuid = st.session_state.money_transfers[idx]["uuid"]
                st.experimental_rerun()  # 立即刷新，执行删除

        # 步骤4：执行删除（标记后立即处理）
        if st.session_state.del_uuid:
            # 找到并删除交易
            trans_to_del = next(t for t in st.session_state.money_transfers if t["uuid"] == st.session_state.del_uuid)
            st.session_state.money_transfers.remove(trans_to_del)
            st.success("Transaction deleted successfully!")
            st.session_state.del_uuid = None  # 重置标记
            st.experimental_rerun()

    st.write("=" * 40)

    # -------------------------- 3. 新增交易（极简表单，确保首次点击生效）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form"):  # 移除clear_on_submit，避免低版本冲突
        # 1. 金额输入（仅基础参数）
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
        # 2. 描述输入
        desc = st.text_input("Description", value="Fundraiser proceeds").strip()
        # 3. 日期选择
        trans_date = st.date_input("Date", value=datetime.today())
        # 4. 处理人输入
        handler = st.text_input("Handled By", value="Pikachu Da Best").strip()
        # 5. 交易类型
        trans_type = st.radio("Type", ["Income", "Expense"], index=0)
        # 提交按钮
        submit_btn = st.form_submit_button("Record Transaction")

        # 步骤5：处理新增逻辑（首次点击立即生效）
        if submit_btn:
            # 校验必填字段（避免空值）
            if not (amount and desc and handler):
                st.error("Required fields: Amount, Description, Handled By!")
            else:
                # 新增交易到会话状态
                st.session_state.money_transfers.append({
                    "uuid": str(uuid.uuid4()),
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                })
                st.session_state.add_success = True
                st.experimental_rerun()  # 立即刷新，显示新增记录

        # 步骤6：显示新增成功提示（刷新后显示，避免首次点击无反应）
        if st.session_state.add_success:
            st.success("Transaction recorded successfully!")
            st.session_state.add_success = False  # 重置提示标记
