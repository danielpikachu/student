import streamlit as st
import pandas as pd
from datetime import datetime

def render_money_transfers():
    # -------------------------- 关键：确保会话状态初始化（首次运行不报错）--------------------------
    # 若 money_transfers 未初始化，强制初始化为空列表（避免首次新增时因状态不存在报错）
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    
    # 自定义 CSS 静态卡片样式（还原视觉效果，兼容所有版本）
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
    
    # -------------------------- 1. 交易记录（上方区域）：首次删除正常执行 --------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 遍历交易记录：用交易唯一属性（日期+金额+处理人）生成删除按钮key，确保首次点击不冲突
        for trans in st.session_state.money_transfers:
            # 生成唯一key：避免同金额/同日期交易的删除按钮key重复（首次点击即可精准删除）
            unique_key = f"trans_del_{trans['Date'].strftime('%Y%m%d')}_{trans['Amount']}_{trans['Handler']}"
            
            # 自定义卡片容器
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            
            # 金额显示：支出红/收入绿，首次新增后立即正确渲染
            amount_display = f"-¥{trans['Amount']:.2f}" if trans["Type"] == "Expense" else f"¥{trans['Amount']:.2f}"
            amount_color = "red" if trans["Type"] == "Expense" else "green"
            
            # 布局：详情+删除按钮
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**Amount**: <span style='color:{amount_color}'>{amount_display}</span>", unsafe_allow_html=True)
                st.write(f"**Description**: {trans['Description']}")
                st.write(f"**Date**: {trans['Date'].strftime('%Y/%m/%d')} | **Handled By**: {trans['Handler']}")
            with col2:
                # 首次点击删除按钮：立即执行移除+刷新，无延迟
                if st.button("Delete", key=unique_key, type="primary"):
                    st.session_state.money_transfers.remove(trans)
                    st.success("Transaction deleted successfully!")
                    st.rerun()  # 强制实时刷新，确保删除后立即更新列表
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # -------------------------- 2. 添加新交易（下方区域）：首次点击立即显示 --------------------------
    st.subheader("Record New Transaction")
    with st.form("new_transaction_form", clear_on_submit=True):
        # 1. 金额输入（默认100.00，必填校验）
        amount = st.number_input(
            "Amount", 
            min_value=0.01, 
            step=0.01, 
            value=100.00, 
            help="This is an expense (negative amount)"
        )
        
        # 2. 描述输入（默认"Fundraiser proceeds"，必填校验）
        description = st.text_input(
            "Description", 
            value="Fundraiser proceeds",
            placeholder="Enter transaction details"
        )
        
        # 3. 日期选择（默认当前日期，格式匹配图片）
        date = st.date_input(
            "Date", 
            value=datetime.today(),
            format="YYYY/MM/DD"
        )
        
        # 4. 处理人输入（默认"Pikachu Da Best"，必填校验）
        handler = st.text_input(
            "Handled By", 
            value="Pikachu Da Best",
            placeholder="Enter name of the person handling the transaction"
        )
        
        # 5. 交易类型（横向排列，默认Income）
        trans_type = st.radio(
            "Transaction Type", 
            ["Income", "Expense"],
            horizontal=True,
            index=0  # 默认选中Income，避免首次选择为空
        )
        
        # 提交按钮：首次点击立即添加到会话状态并显示
        submit_btn = st.form_submit_button(
            "Record Transaction", 
            use_container_width=True,
            type="primary"
        )
        
        # 表单验证：首次提交若必填项完整，立即添加记录
        if submit_btn:
            # 严格校验必填字段（避免空值添加到列表）
            if not amount or not description.strip() or not handler.strip():
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                # 新增记录到会话状态（首次添加后立即被上方列表读取）
                new_transaction = {
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),  # 保留2位小数，避免金额精度问题
                    "Handler": handler.strip(),
                    "Description": description.strip()
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                # 强制刷新页面：确保首次新增后立即在上方交易记录中显示
                st.rerun()
