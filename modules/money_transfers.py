import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    # 页面主标题：匹配图片"Financial Transactions"
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 1. 交易记录（上方区域）--------------------------
    st.subheader("Transaction History")
    # 无交易记录时显示图片同款提示文案
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 遍历展示所有交易记录（卡片式布局）
        for i, trans in enumerate(st.session_state.money_transfers):
            with st.card():
                # 金额显示逻辑：支出标红带负号，收入标绿（匹配图片"支出为负金额"的提示）
                amount_display = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
                amount_color = "red" if trans["Type"] == "Expense" else "green"
                
                # 布局：左侧交易详情，右侧删除按钮
                col1, col2 = st.columns([4, 1])
                with col1:
                    # 金额（带颜色区分）
                    st.markdown(f"**Amount**: <span style='color:{amount_color}'>{amount_display}</span>", unsafe_allow_html=True)
                    # 描述、日期、处理人（匹配图片展示字段）
                    st.write(f"**Description**: {trans['Description']}")
                    st.write(f"**Date**: {trans['Date'].strftime('%Y/%m/%d')} | **Handled By**: {trans['Handler']}")
                with col2:
                    # 删除按钮：点击后实时移除并刷新
                    if st.button("Delete", key=f"trans_del_{i}", type="primary"):
                        st.session_state.money_transfers.remove(trans)
                        st.success("Transaction deleted successfully!")
                        st.rerun()  # 替代旧版 st.experimental_rerun()
    
    # 分割线：区分交易记录与添加功能区域
    st.divider()
    
    # -------------------------- 2. 添加新交易（下方区域）--------------------------
    st.subheader("Record New Transaction")
    # 表单：严格匹配图片字段与默认值
    with st.form("new_transaction_form", clear_on_submit=True):
        # 1. 金额输入框（默认100.00，匹配图片初始值）
        amount = st.number_input(
            "Amount", 
            min_value=0.01,  # 确保金额为正数，支出通过类型区分负号
            step=0.01, 
            value=100.00, 
            help="This is an expense (negative amount)"  # 图片同款提示文案
        )
        
        # 2. 描述输入框（默认"Fundraiser proceeds"，匹配图片）
        description = st.text_input(
            "Description", 
            value="Fundraiser proceeds",
            placeholder="Enter transaction details"
        )
        
        # 3. 日期选择（默认当前日期，格式匹配图片"2025/10/29"）
        date = st.date_input(
            "Date", 
            value=datetime.today(),
            format="YYYY/MM/DD"
        )
        
        # 4. 处理人输入框（默认"Pikachu Da Best"，匹配图片）
        handler = st.text_input(
            "Handled By", 
            value="Pikachu Da Best",
            placeholder="Enter name of the person handling the transaction"
        )
        
        # 5. 交易类型选择（提示支出对应负金额，与图片逻辑一致）
        trans_type = st.radio(
            "Transaction Type", 
            ["Income", "Expense"],
            horizontal=True  # 横向排列，优化界面紧凑度
        )
        
        # 提交按钮：文字改为"Record Transaction"（匹配图片）
        submit_btn = st.form_submit_button(
            "Record Transaction", 
            use_container_width=True,  # 宽按钮，提升易用性
            type="primary"
        )
        
        # 表单验证与提交逻辑
        if submit_btn:
            # 校验必填字段（金额、描述、处理人）
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                # 新增交易到会话状态（保留2位小数，确保金额精度）
                st.session_state.money_transfers.append({
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                })
                st.success("Transaction recorded successfully!")
