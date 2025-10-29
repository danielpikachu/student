import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    # 页面标题：匹配图片中的"Financial Transactions"
    st.header("Financial Transactions")
    st.divider()
    
    # 子选项卡调整：仅保留「交易记录」和「添加新交易」（图片无统计功能）
    records_tab, add_tab = st.tabs(["Transaction History", "Record New Transaction"])
    
    # -------------------------- 1. 交易记录标签页（Transaction History）--------------------------
    with records_tab:
        st.subheader("Transaction History")
        # 若无交易记录：显示图片中的"No financial transactions recorded yet"
        if not st.session_state.money_transfers:
            st.info("No financial transactions recorded yet")
        else:
            # 交易记录列表：简化展示（匹配图片核心字段）
            for i, trans in enumerate(st.session_state.money_transfers):
                with st.card():
                    # 金额与类型：支出标红，收入标绿（区分正负属性）
                    amount_display = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
                    amount_color = "red" if trans["Type"] == "Expense" else "green"
                    
                    # 布局：左侧核心信息，右侧删除按钮
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**Amount**: <span style='color:{amount_color}'>{amount_display}</span>", unsafe_allow_html=True)
                        st.write(f"**Description**: {trans['Description']}")
                        st.write(f"**Date**: {trans['Date'].strftime('%Y/%m/%d')} | **Handled By**: {trans['Handler']}")
                    with col2:
                        # 删除按钮：点击后刷新页面
                        if st.button("Delete", key=f"trans_del_{i}", type="primary"):
                            st.session_state.money_transfers.remove(trans)
                            st.success("Transaction deleted successfully!")
                            st.rerun()  # 替代旧版 st.experimental_rerun()
    
    # -------------------------- 2. 添加新交易标签页（Record New Transaction）--------------------------
    with add_tab:
        st.subheader("Record New Transaction")
        # 表单：严格匹配图片中的字段（金额、描述、收支类型、日期、处理人）
        with st.form("new_transaction_form", clear_on_submit=True):
            # 第一行：金额输入框（默认100.00，匹配图片）
            amount = st.number_input(
                "Amount", 
                min_value=0.01, 
                step=0.01, 
                value=100.00,  # 默认值设为100.00
                help="Enter the transaction amount (positive number)"
            )
            
            # 第二行：描述输入框（默认"Fundraiser proceeds"，匹配图片）
            description = st.text_input(
                "Description", 
                value="Fundraiser proceeds",  # 默认描述内容
                help="Enter details about the transaction"
            )
            
            # 第三行：收支类型选择（单选按钮，默认"收入"，匹配图片的"expense为负金额"逻辑）
            trans_type = st.radio(
                "Transaction Type", 
                ["Income", "Expense"],
                help="Select 'Expense' for negative amount transactions"
            )
            
            # 第四行：日期选择（默认当前日期，格式匹配图片的2025/10/29）
            date = st.date_input(
                "Date", 
                value=datetime.today(),
                format="YYYY/MM/DD"  # 日期显示格式与图片一致
            )
            
            # 第五行：处理人输入（默认"Pikachu Da Best"，匹配图片）
            handler = st.text_input(
                "Handled By", 
                value="Pikachu Da Best",  # 默认处理人
                help="Enter the name of the person handling the transaction"
            )
            
            # 提交按钮：文字改为"Record Transaction"（匹配图片）
            submit_btn = st.form_submit_button(
                "Record Transaction", 
                use_container_width=True,
                type="primary"
            )
            
            # 表单验证与提交逻辑
            if submit_btn:
                # 校验必填字段（金额、描述、处理人）
                if not amount or not description or not handler:
                    st.error("Please fill in all required fields (Amount, Description, Handled By)!")
                else:
                    # 新增交易到会话状态
                    st.session_state.money_transfers.append({
                        "Date": date,                  # 日期（datetime类型）
                        "Type": trans_type,            # 类型（Income/Expense）
                        "Amount": round(amount, 2),    # 金额（保留2位小数）
                        "Handler": handler,            # 处理人
                        "Description": description     # 描述
                    })
                    st.success("Transaction recorded successfully!")
