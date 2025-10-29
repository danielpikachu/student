import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 生成唯一ID，避免删除操作冲突

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    # 用于标记待删除的交易ID（避免表格渲染时直接修改列表）
    if "to_delete_uuid" not in st.session_state:
        st.session_state.to_delete_uuid = None
    
    # 页面标题与分割线
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 2. 交易记录（表格形式，带删除按钮）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理交易数据，生成表格所需格式（不含直接嵌入的按钮）
        table_rows = []
        for trans in st.session_state.money_transfers:
            # 金额处理：支出标红带负号，收入标绿带正号（用Markdown格式）
            if trans["Type"] == "Expense":
                amount_text = f"-¥{trans['Amount']:.2f}"
                amount_display = f"<span style='color:red'>{amount_text}</span>"
            else:
                amount_text = f"¥{trans['Amount']:.2f}"
                amount_display = f"<span style='color:green'>{amount_text}</span>"
            
            # 构造表格行（包含唯一uuid，用于后续删除定位）
            table_rows.append({
                "UUID": trans["uuid"],  # 隐藏列，用于定位删除的交易
                "Date": trans["Date"].strftime("%Y/%m/%d"),
                "Amount": amount_display,
                "Description": trans["Description"],
                "Handled By": trans["Handler"],
                "Delete": False  # 复选框列，用于标记是否删除（替代直接按钮）
            })
        
        # 步骤2：用 st.data_editor 渲染表格（支持复选框列，避免组件嵌入错误）
        edited_df = st.data_editor(
            pd.DataFrame(table_rows),
            # 配置列属性：隐藏UUID列，设置复选框列
            column_config={
                "UUID": st.column_config.HiddenColumn(),  # 隐藏唯一标识列，不显示给用户
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Amount": st.column_config.MarkdownColumn("Amount", width="small"),  # 支持Markdown渲染颜色
                "Description": st.column_config.TextColumn("Description", width="medium"),
                "Handled By": st.column_config.TextColumn("Handled By", width="small"),
                "Delete": st.column_config.CheckboxColumn("Delete", width="small")  # 复选框列，用于标记删除
            },
            disabled=["UUID", "Date", "Amount", "Description", "Handled By"],  # 仅开放Delete列编辑
            index=False,  # 隐藏默认索引
            use_container_width=True,
            num_rows="fixed"  # 固定行数，不允许用户新增行
        )
        
        # 步骤3：处理删除逻辑（检测复选框选中状态，执行删除）
        # 筛选出被标记为"Delete=True"的行
        deleted_rows = edited_df[edited_df["Delete"] == True]
        if not deleted_rows.empty:
            # 遍历待删除行，根据UUID从会话状态中移除对应交易
            for _, row in deleted_rows.iterrows():
                trans_to_delete = next(
                    (t for t in st.session_state.money_transfers if t["uuid"] == row["UUID"]),
                    None
                )
                if trans_to_delete:
                    st.session_state.money_transfers.remove(trans_to_delete)
            # 显示删除成功提示并刷新页面
            st.success(f"Successfully deleted {len(deleted_rows)} transaction(s)!")
            st.rerun()
    
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
        
        # 表单验证与新增逻辑（添加uuid确保删除定位准确）
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                new_transaction = {
                    "uuid": str(uuid.uuid4()),  # 唯一ID，用于删除定位
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                st.rerun()  # 新增后实时刷新表格
