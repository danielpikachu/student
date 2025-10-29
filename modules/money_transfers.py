import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 生成唯一ID，避免删除按钮key重复

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    # 存储待删除的交易UUID（避免渲染时直接修改列表）
    if "delete_uuid" not in st.session_state:
        st.session_state.delete_uuid = None

    # 页面标题与分割线
    st.header("Financial Transactions")
    st.divider()

    # -------------------------- 2. 交易记录（表格展示+独立删除按钮）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理表格数据（仅包含展示字段，金额带颜色标签）
        table_data = []
        delete_buttons = []  # 存储每个交易的删除按钮
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 金额颜色处理：支出红/收入绿（HTML标签，后续表格渲染时生效）
            if trans["Type"] == "Expense":
                amount = f"<span style='color:red'>-¥{trans['Amount']:.2f}</span>"
            else:
                amount = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>"
            
            # 构造表格行数据（不含按钮，仅纯文本/HTML）
            table_data.append({
                "No.": idx + 1,  # 序号列，方便对应删除按钮
                "Date": trans["Date"].strftime("%Y/%m/%d"),
                "Amount": amount,
                "Description": trans["Description"],
                "Handled By": trans["Handler"]
            })
            
            # 为每个交易生成唯一删除按钮（key含UUID，绝对不重复）
            btn_key = f"del_btn_{trans['uuid']}"
            delete_buttons.append(
                st.button(
                    f"Delete #{idx + 1}",  # 按钮文字带序号，对应表格行
                    key=btn_key,
                    type="primary",
                    use_container_width=True
                )
            )

        # 步骤2：渲染表格（用st.dataframe，兼容所有版本）
        # 关键：设置escape=False，允许解析HTML颜色标签
        st.dataframe(
            pd.DataFrame(table_data),
            column_config={
                "No.": st.column_config.TextColumn("No.", width="small"),
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Description": st.column_config.TextColumn("Description", width="medium"),
                "Handled By": st.column_config.TextColumn("Handled By", width="small")
            },
            index=False,  # 隐藏默认索引
            escape=False,  # 允许HTML渲染（金额颜色）
            use_container_width=True
        )

        # 步骤3：渲染删除按钮（与表格序号一一对应）
        st.subheader("Delete Transactions")
        st.write("Click the button below to delete the corresponding transaction (match the 'No.' in the table):")
        # 按钮分行显示，每行一个，与表格序号对应
        for idx, (btn, trans) in enumerate(zip(delete_buttons, st.session_state.money_transfers)):
            if btn:
                # 记录待删除的交易UUID，避免渲染时直接修改列表
                st.session_state.delete_uuid = trans["uuid"]

        # 步骤4：执行删除逻辑（在表格和按钮渲染后处理，避免渲染冲突）
        if st.session_state.delete_uuid:
            # 找到待删除的交易并移除
            trans_to_delete = next(
                (t for t in st.session_state.money_transfers if t["uuid"] == st.session_state.delete_uuid),
                None
            )
            if trans_to_delete:
                st.session_state.money_transfers.remove(trans_to_delete)
                st.success(f"Transaction #{idx + 1} deleted successfully!")
                # 重置删除标记，避免重复删除
                st.session_state.delete_uuid = None
                st.rerun()  # 刷新页面，更新表格和按钮

    st.divider()

    # -------------------------- 3. 添加新交易（保持原功能，兼容所有版本）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_transaction_form", clear_on_submit=True):
        # 1. 金额输入（默认100.00，最小0.01）
        amount = st.number_input(
            "Amount",
            min_value=0.01,
            step=0.01,
            value=100.00,
            help="This is an expense (negative amount)"
        )

        # 2. 描述输入（默认"Fundraiser proceeds"，去空格校验）
        description = st.text_input(
            "Description",
            value="Fundraiser proceeds",
            placeholder="Enter transaction details"
        ).strip()

        # 3. 日期选择（格式YYYY/MM/DD，默认当前日期）
        date = st.date_input(
            "Date",
            value=datetime.today(),
            format="YYYY/MM/DD"
        )

        # 4. 处理人输入（默认"Pikachu Da Best"，去空格校验）
        handler = st.text_input(
            "Handled By",
            value="Pikachu Da Best",
            placeholder="Enter name of the person handling the transaction"
        ).strip()

        # 5. 交易类型（横向排列，默认选中Income）
        trans_type = st.radio(
            "Transaction Type",
            ["Income", "Expense"],
            horizontal=True,
            index=0
        )

        # 提交按钮
        submit_btn = st.form_submit_button(
            "Record Transaction",
            use_container_width=True,
            type="primary"
        )

        # 表单验证与新增逻辑（添加UUID，用于删除按钮key）
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                new_transaction = {
                    "uuid": str(uuid.uuid4()),  # 唯一ID，确保删除按钮key不重复
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                st.rerun()  # 新增后刷新，更新表格
