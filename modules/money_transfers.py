import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 1. 交易记录（上方区域）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        for i, trans in enumerate(st.session_state.money_transfers):
            # 用 expander 替代 card，默认展开（expanded=True），标题显示核心信息
            with st.expander(
                label=f"{'Expense' if trans['Type'] == 'Expense' else 'Income'}: ¥{trans['Amount']:.2f} | {trans['Date'].strftime('%Y/%m/%d')}",
                expanded=True
            ):
                # 金额颜色区分：支出红、收入绿
                amount_display = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
                amount_color = "red" if trans["Type"] == "Expense" else "green"
                
                # 交易详情布局
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**Amount**: <span style='color:{amount_color}'>{amount_display}</span>", unsafe_allow_html=True)
                    st.write(f"**Description**: {trans['Description']}")
                    st.write(f"**Handled By**: {trans['Handler']}")
                with col2:
                    # 删除按钮：点击实时移除并刷新
                    if st.button("Delete", key=f"trans_del_{i}", type="primary"):
                        st.session_state.money_transfers.remove(trans)
                        st.success("Transaction deleted successfully!")
                        st.rerun()
    
    st.divider()
    
    # -------------------------- 2. 添加新交易（下方区域）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_transaction_form", clear_on_submit=True):
        # 1. 金额输入（默认100.00，匹配图片）
        amount = st.number_input(
            "Amount", 
            min_value=0.01, 
            step=0.01, 
            value=100.00, 
            help="This is an expense (negative amount)"
        )
        
        # 2. 描述输入（默认"Fundraiser proceeds"）
        description = st.text_input(
            "Description", 
            value="Fundraiser proceeds",
            placeholder="Enter transaction details"
        )
        
        # 3. 日期选择（格式 YYYY/MM/DD）
        date = st.date_input(
            "Date", 
            value=datetime.today(),
            format="YYYY/MM/DD"
        )
        
        # 4. 处理人输入（默认"Pikachu Da Best"）
        handler = st.text_input(
            "Handled By", 
            value="Pikachu Da Best",
            placeholder="Enter name of the person handling the transaction"
        )
        
        # 5. 交易类型（横向排列）
        trans_type = st.radio(
            "Transaction Type", 
            ["Income", "Expense"],
            horizontal=True
        )
        
        # 提交按钮
        submit_btn = st.form_submit_button(
            "Record Transaction", 
            use_container_width=True,
            type="primary"
        )
        
        # 表单验证与提交
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                st.session_state.money_transfers.append({
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                })
                st.success("Transaction recorded successfully!")
