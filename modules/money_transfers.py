import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 用于生成唯一ID，彻底避免key重复

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        # 新增交易时自动添加唯一ID（uuid），用于生成不重复的删除按钮key
        st.session_state.money_transfers = []
    
    # 自定义CSS卡片样式（兼容所有Streamlit版本）
    st.markdown("""
        <style>
        .custom-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 页面标题与分割线
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 2. 交易记录（上方区域）：删除按钮key绝对唯一 --------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 遍历交易记录：用内置唯一ID生成删除按钮key，彻底避免重复
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 关键：用交易自带的uuid（新增时生成）+ 索引生成key，确保绝对不重复
            unique_btn_key = f"trans_del_{trans['uuid']}_{idx}"
            
            # 自定义卡片容器
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            
            # 金额显示：支出红/收入绿
            amount_display = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
            amount_color = "red" if trans["Type"] == "Expense" else "green"
            
            # 布局：详情+删除按钮
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**Amount**: <span style='color:{amount_color}'>{amount_display}</span>", unsafe_allow_html=True)
                st.write(f"**Description**: {trans['Description']}")
                st.write(f"**Date**: {trans['Date'].strftime('%Y/%m/%d')} | **Handled By**: {trans['Handler']}")
            with col2:
                # 首次点击删除：立即执行并实时刷新
                if st.button("Delete", key=unique_btn_key, type="primary"):
                    st.session_state.money_transfers.remove(trans)
                    st.success("Transaction deleted successfully!")
                    st.rerun()  # 强制刷新，确保删除后列表立即更新
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # -------------------------- 3. 添加新交易（下方区域）：首次新增立即显示 --------------------------
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
        ).strip()  # 去除前后空格，避免空字符串
        
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
        ).strip()  # 去除前后空格
        
        # 5. 交易类型（横向排列，默认选中Income）
        trans_type = st.radio(
            "Transaction Type", 
            ["Income", "Expense"],
            horizontal=True,
            index=0  # 避免首次无选择
        )
        
        # 提交按钮：首次点击立即添加
        submit_btn = st.form_submit_button(
            "Record Transaction", 
            use_container_width=True,
            type="primary"
        )
        
        # 表单验证与新增逻辑
        if submit_btn:
            # 校验必填字段（避免空值）
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                # 关键：新增交易时自动添加uuid（绝对唯一标识）
                new_transaction = {
                    "uuid": str(uuid.uuid4()),  # 生成唯一ID，用于删除按钮key
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),  # 保留2位小数，避免精度问题
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                st.rerun()  # 强制刷新，确保首次新增后立即显示在列表中
