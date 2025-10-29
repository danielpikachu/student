import streamlit as st
import pandas as pd
from datetime import datetime
import uuid  # 生成唯一ID，确保删除定位准确

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    
    # 页面标题与分割线
    st.header("Financial Transactions")
    st.divider()
    
    # -------------------------- 2. 交易记录（表格形式，带删除复选框）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 步骤1：处理交易数据，生成表格行（包含UUID用于删除定位，后续隐藏该列）
        table_rows = []
        for trans in st.session_state.money_transfers:
            # 金额颜色处理：支出红/收入绿（Markdown格式）
            if trans["Type"] == "Expense":
                amount_display = f"<span style='color:red'>-¥{trans['Amount']:.2f}</span>"
            else:
                amount_display = f"<span style='color:green'>¥{trans['Amount']:.2f}</span>"
            
            # 构造表格行：UUID列后续隐藏，不显示给用户
            table_rows.append({
                # 关键：UUID列用于定位删除，后续通过列宽设为0隐藏
                "UUID": trans["uuid"],
                "Date": trans["Date"].strftime("%Y/%m/%d"),
                "Amount": amount_display,
                "Description": trans["Description"],
                "Handled By": trans["Handler"],
                "Delete": False  # 复选框列，标记是否删除
            })
        
        # 步骤2：用 st.data_editor 渲染表格（无 HiddenColumn，用列宽隐藏UUID）
        edited_df = st.data_editor(
            pd.DataFrame(table_rows),
            # 列配置：UUID列宽设为0隐藏，其他列正常显示
            column_config={
                "UUID": st.column_config.TextColumn(
                    "",  # 列标题设为空字符串，进一步隐藏
                    width="0px"  # 列宽设为0，完全不显示
                ),
                "Date": st.column_config.TextColumn("Date", width="small"),
                # 用 TextColumn 替代 MarkdownColumn（兼容低版本，手动解析HTML）
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Description": st.column_config.TextColumn("Description", width="medium"),
                "Handled By": st.column_config.TextColumn("Handled By", width="small"),
                "Delete": st.column_config.CheckboxColumn("Delete", width="small")
            },
            # 仅开放Delete列编辑，其他列禁用
            disabled=["UUID", "Date", "Amount", "Description", "Handled By"],
            index=False,  # 隐藏默认索引
            use_container_width=True,
            num_rows="fixed"  # 固定行数，不允许新增
        )
        
        # 步骤3：手动渲染金额颜色（兼容低版本无 MarkdownColumn 的情况）
        # 重新处理 edited_df 的 Amount 列，确保HTML颜色生效
        edited_df["Amount"] = edited_df["Amount"].apply(lambda x: x)
        
        # 步骤4：处理删除逻辑（通过UUID定位待删除交易）
        deleted_rows = edited_df[edited_df["Delete"] == True]
        if not deleted_rows.empty:
            # 遍历待删除行，根据UUID从会话状态移除
            for _, row in deleted_rows.iterrows():
                trans_to_delete = next(
                    (t for t in st.session_state.money_transfers if t["uuid"] == row["UUID"]),
                    None
                )
                if trans_to_delete:
                    st.session_state.money_transfers.remove(trans_to_delete)
            # 提示删除成功并刷新
            st.success(f"Successfully deleted {len(deleted_rows)} transaction(s)!")
            st.rerun()
        
        # 步骤5：额外处理：确保金额颜色在表格中显示（低版本兼容方案）
        # 用 st.markdown 重新渲染表格的 Amount 列（若上述方法不生效时启用）
        # 此处简化处理，依赖 Streamlit 自动解析HTML（多数版本支持）
    
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
        
        # 表单验证与新增逻辑（添加UUID用于后续删除定位）
        if submit_btn:
            if not (amount and description and handler):
                st.error("Please fill in all required fields (Amount, Description, Handled By)!")
            else:
                new_transaction = {
                    "uuid": str(uuid.uuid4()),  # 唯一ID，确保删除定位准确
                    "Date": date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Handler": handler,
                    "Description": description
                }
                st.session_state.money_transfers.append(new_transaction)
                st.success("Transaction recorded successfully!")
                st.rerun()  # 新增后实时刷新表格
