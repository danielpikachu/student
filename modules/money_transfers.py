import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    # 核心：所有状态初始化，避免首次访问时未定义
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 存储交易记录
    if "add_status" not in st.session_state:
        st.session_state.add_status = "idle"  # 新增状态：idle/success/error
    if "add_msg" not in st.session_state:
        st.session_state.add_msg = ""  # 新增提示消息
    if "del_idx" not in st.session_state:
        st.session_state.del_idx = -1  # 待删除的交易索引（-1表示无）

    # 页面标题（基础组件，全版本兼容）
    st.header("Financial Transactions")
    st.write("=" * 40)

    # -------------------------- 2. 先处理删除操作（无刷新，直接修改列表）--------------------------
    # 若有标记待删除的索引，直接从列表中移除（无需刷新）
    if st.session_state.del_idx != -1 and st.session_state.del_idx < len(st.session_state.money_transfers):
        st.session_state.money_transfers.pop(st.session_state.del_idx)
        st.success("Transaction deleted successfully!")
        st.session_state.del_idx = -1  # 重置删除标记

    # -------------------------- 3. 交易记录（表格+删除按钮，无刷新）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理表格数据（纯列表格式，无复杂配置）
        table_data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 金额颜色：用HTML标签，后续通过escape=False渲染
            amount_color = "red" if trans["Type"] == "Expense" else "green"
            amount_text = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
            amount_html = f"<span style='color:{amount_color}'>{amount_text}</span>"
            
            # 表格行：直接用列表存储，避免字典转DataFrame的兼容性问题
            table_data.append([
                idx + 1,  # 序号
                trans["Date"].strftime("%Y/%m/%d"),  # 日期
                amount_html,  # 金额（带颜色）
                trans["Description"],  # 描述
                trans["Handler"]  # 处理人
            ])

        # 步骤2：渲染表格（移除所有可选参数，仅保留最基础功能）
        # 关键：用列表生成DataFrame，列名直接定义，无任何高版本参数
        st.dataframe(
            pd.DataFrame(
                table_data,
                columns=["No.", "Date", "Amount", "Description", "Handled By"]
            ),
            index=False,  # 隐藏默认索引（必选参数，全版本支持）
            escape=False  # 允许解析HTML标签（必选参数，全版本支持）
        )

        # 步骤3：删除按钮区域（点击后仅标记索引，不刷新）
        st.write("Click to delete transaction:")
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 生成唯一按钮key（用UUID确保不重复）
            btn_key = f"del_btn_{trans['uuid']}"
            # 点击按钮后，仅更新del_idx状态，不刷新页面
            if st.button(f"Delete Transaction #{idx + 1}", key=btn_key):
                st.session_state.del_idx = idx  # 标记待删除的索引
                # 强制重新渲染当前函数（无刷新，仅重跑代码）
                return render_money_transfers()

    st.write("=" * 40)

    # -------------------------- 4. 新增交易（表单+状态标记，无刷新）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form"):  # 纯基础表单，无任何可选参数
        # 基础输入组件：仅用必选参数，全版本兼容
        amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
        desc = st.text_input("Description", value="Fundraiser proceeds").strip()
        trans_date = st.date_input("Date", value=datetime.today())
        handler = st.text_input("Handled By", value="Pikachu Da Best").strip()
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
        submit_btn = st.form_submit_button("Record Transaction")

        # 步骤4：处理表单提交（无刷新，仅更新状态）
        if submit_btn:
            # 校验必填字段
            if not amount or not desc or not handler:
                st.session_state.add_status = "error"
                st.session_state.add_msg = "Required fields: Amount, Description, Handled By!"
            else:
                # 新增交易到列表（直接修改，无需刷新）
                st.session_state.money_transfers.append({
                    "uuid": str(uuid.uuid4()),  # 唯一ID，用于按钮key
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                })
                st.session_state.add_status = "success"
                st.session_state.add_msg = "Transaction recorded successfully!"
            # 强制重新渲染当前函数，显示提示和新记录
            return render_money_transfers()

    # 步骤5：显示新增提示（根据add_status状态渲染）
    if st.session_state.add_status == "success":
        st.success(st.session_state.add_msg)
        # 重置新增状态，避免重复显示提示
        st.session_state.add_status = "idle"
    elif st.session_state.add_status == "error":
        st.error(st.session_state.add_msg)
        st.session_state.add_status = "idle"
