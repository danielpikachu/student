import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 生成唯一ID，避免删除按钮key重复

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    if "delete_uuid" not in st.session_state:
        st.session_state.delete_uuid = None  # 存储待删除交易的UUID

    # 页面标题与分割线（基础组件，全版本兼容）
    st.header("Financial Transactions")
    st.write("-" * 50)  # 用分割线替代 st.divider()（部分极低版本无divider）

    # -------------------------- 2. 交易记录（表格+独立删除按钮，全版本兼容）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理表格数据（仅基础字段，避免复杂配置）
        table_data = []
        delete_btns = []  # 存储删除按钮，与表格行一一对应
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 金额颜色处理：用HTML标签，后续通过escape=False渲染
            if trans["Type"] == "Expense":
                amount = f"<span style='color:red'>-¥{trans['Amount']:.2f}</span>"
            else:
                amount = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>"
            
            # 表格数据：仅包含基础列，无复杂配置
            table_data.append({
                "No.": idx + 1,  # 序号，用于匹配删除按钮
                "Date": trans["Date"].strftime("%Y/%m/%d"),
                "Amount": amount,
                "Description": trans["Description"],
                "Handled By": trans["Handler"]
            })
            
            # 生成唯一删除按钮（key含UUID，绝对不重复）
            btn_key = f"del_{trans['uuid']}_{idx}"
            delete_btns.append(
                st.button(
                    f"Delete Transaction #{idx + 1}",  # 按钮文字带序号，清晰对应表格
                    key=btn_key,
                    use_container_width=True
                )
            )

        # 步骤2：渲染表格（移除所有高版本参数，仅保留基础功能）
        # 关键：仅用st.dataframe基础参数，兼容所有版本
        st.dataframe(
            pd.DataFrame(table_data),
            index=False,  # 隐藏默认索引
            escape=False,  # 允许解析HTML颜色标签
            width=None,    # 宽度自适应（低版本兼容写法）
            height=None    # 高度自适应
        )

        # 步骤3：显示删除按钮区域（与表格序号对应）
        st.subheader("Delete Option")
        st.write("Click the button to delete the corresponding transaction (match 'No.' in the table):")
        # 分行显示删除按钮，确保与表格行对齐
        for btn in delete_btns:
            if btn:
                # 找到被点击按钮对应的交易UUID
                clicked_idx = delete_btns.index(btn)
                clicked_trans = st.session_state.money_transfers[clicked_idx]
                st.session_state.delete_uuid = clicked_trans["uuid"]

        # 步骤4：执行删除逻辑（渲染后处理，避免冲突）
        if st.session_state.delete_uuid:
            # 定位并删除交易
            trans_to_del = next(
                (t for t in st.session_state.money_transfers if t["uuid"] == st.session_state.delete_uuid),
                None
            )
            if trans_to_del:
                st.session_state.money_transfers.remove(trans_to_del)
                st.success(f"Transaction deleted successfully!")
                st.session_state.delete_uuid = None  # 重置删除标记
                st.experimental_rerun()  # 低版本兼容的刷新方式（替代st.rerun()）

    # 基础分割线（兼容极低版本）
    st.write("-" * 50)

    # -------------------------- 3. 添加新交易（基础表单，全版本兼容）--------------------------
    st.subheader("Record New Transaction")
    # 用基础表单组件，不使用复杂配置
    with st.form("new_trans_form", clear_on_submit=True):
        # 1. 金额输入（基础参数，全版本兼容）
        amount = st.number_input(
            "Amount (¥)",
            min_value=0.01,
            step=0.01,
            value=100.00,
            help="This is an expense (negative amount)"
        )

        # 2. 描述输入（基础文本框）
        description = st.text_input(
            "Description",
            value="Fundraiser proceeds"
        ).strip()  # 去空格，避免无效输入

        # 3. 日期选择（基础日期组件）
        date = st.date_input(
            "Transaction Date",
            value=datetime.today()
        )

        # 4. 处理人输入（基础文本框）
        handler = st.text_input(
            "Handled By",
            value="Pikachu Da Best"
        ).strip()

        # 5. 交易类型（基础单选按钮）
        trans_type = st.radio(
            "Transaction Type",
            ["Income", "Expense"],
            index=0  # 默认选中Income
        )

        # 提交按钮（基础按钮，无复杂样式）
        submit_btn = st.form_submit_button("Record Transaction")

        # 表单验证与提交逻辑
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields: Amount, Description, Handled By!")
            else:
                # 新增交易（带UUID，用于后续删除）
                new_trans = {
                    "uuid": str(uuid.uuid4()),
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_trans)
                st.success("Transaction recorded successfully!")
                st.experimental_rerun()  # 低版本兼容的刷新
