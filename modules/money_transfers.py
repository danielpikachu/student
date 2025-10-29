import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 生成唯一ID，避免删除按钮key重复

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    
    # 页面标题与分割线
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 2. 交易记录（表格形式，带删除按钮）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理交易数据，添加「金额显示（带正负/颜色）」和「删除按钮列」
        table_data = []
        for trans in st.session_state.money_transfers:
            # 金额处理：支出显示负号+红色，收入显示正号+绿色（表格中用Markdown渲染颜色）
            if trans["Type"] == "Expense":
                amount_display = f"-¥{trans['Amount']:.2f}"
                amount_markdown = f"<span style='color:red'>{amount_display}</span>"
            else:
                amount_display = f"¥{trans['Amount']:.2f}"
                amount_markdown = f"<span style='color:green'>{amount_display}</span>"
            
            # 为每笔交易生成唯一删除按钮key（用uuid确保不重复）
            delete_btn_key = f"trans_del_{trans['uuid']}"
            
            # 构造表格行数据：包含所有需展示字段+删除按钮
            table_data.append({
                "Date": trans["Date"].strftime("%Y/%m/%d"),  # 日期格式化
                "Amount": amount_markdown,  # 带颜色的金额
                "Description": trans["Description"],
                "Handled By": trans["Handler"],
                "Action": st.button("Delete", key=delete_btn_key, type="primary", use_container_width=True)
            })
        
        # 步骤2：用Streamlit的dataframe渲染表格（开启HTML支持以显示颜色）
        # 关键：设置escape=False，允许渲染Markdown格式的金额（颜色+正负号）
        st.dataframe(
            pd.DataFrame(table_data),
            column_config={
                # 配置列宽和对齐方式，优化表格视觉效果
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Description": st.column_config.TextColumn("Description", width="medium"),
                "Handled By": st.column_config.TextColumn("Handled By", width="small"),
                "Action": st.column_config.TextColumn("Action", width="small")
            },
            index=False,  # 隐藏默认索引列
            escape=False,  # 允许渲染HTML（颜色金额）
            use_container_width=True  # 表格宽度适应页面
        )
        
        # 步骤3：检查删除按钮点击事件，执行删除逻辑
        for trans in st.session_state.money_transfers:
            delete_btn_key = f"trans_del_{trans['uuid']}"
            if st.session_state.get(delete_btn_key, False):  # 检测按钮是否被点击
                st.session_state.money_transfers.remove(trans)
                st.success(f"Transaction on {trans['Date'].strftime('%Y/%m/%d')} deleted successfully!")
                st.rerun()  # 实时刷新表格，移除已删除记录
    
    st.divider()
    
    # -------------------------- 3. 添加新交易（下方区域，保持原功能）--------------------------
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
        
        # 表单验证与新增逻辑（添加uuid确保删除按钮key唯一）
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                new_transaction = {
                    "uuid": str(uuid.uuid4()),  # 唯一ID，用于删除按钮key
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                st.rerun()  # 新增后实时刷新表格
