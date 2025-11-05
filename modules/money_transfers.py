import streamlit as st
from datetime import datetime
import uuid
import sys
import os
import time

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_money_transfers():
    # 初始化会话状态
    if 'money_transfers' not in st.session_state:
        st.session_state.money_transfers = []
    if 'render_counter' not in st.session_state:
        st.session_state.render_counter = 0  # 用于跟踪渲染次数，确保key随渲染更新
    
    # 初始化Google Sheets连接
    sheet_handler = None
    transfers_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        transfers_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="MoneyTransfers"
        )
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")

    # 从Google Sheets同步数据（仅首次加载时）
    if transfers_sheet and not st.session_state.money_transfers:
        try:
            time.sleep(0.1)
            all_data = transfers_sheet.get_all_values()
            
            if not all_data or all_data[0] != ["uuid", "date", "type", "amount", "description", "handler"]:
                transfers_sheet.clear()
                transfers_sheet.append_row(["uuid", "date", "type", "amount", "description", "handler"])
                records = []
            else:
                records = [
                    {
                        "uuid": row[0],
                        "Date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "Type": row[2],
                        "Amount": float(row[3]),
                        "Description": row[4],
                        "Handler": row[5]
                    } 
                    for row in all_data[1:] if row and row[0]
                ]
            
            st.session_state.money_transfers = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 显示交易历史
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        with st.container():
            # 表头
            cols = st.columns([0.5, 1.5, 1.5, 1.2, 2, 1.5, 1.2])
            headers = ["No.", "Date", "Amount ($)", "Type", "Description", "Handled By", "Action"]
            for col, header in zip(cols, headers):
                col.write(f"**{header}**")
            
            # 为每个记录生成绝对唯一的删除按钮key
            for idx, trans in enumerate(st.session_state.money_transfers):
                with st.container():
                    row_cols = st.columns([0.5, 1.5, 1.5, 1.2, 2, 1.5, 1.2])
                    
                    # 显示数据
                    row_cols[0].write(idx + 1)
                    row_cols[1].write(trans["Date"].strftime("%Y-%m-%d"))
                    row_cols[2].write(f"${trans['Amount']:.2f}")
                    row_cols[3].write(trans["Type"])
                    row_cols[4].write(trans["Description"])
                    row_cols[5].write(trans["Handler"])
                    
                    # 关键修复：使用渲染计数器+记录UUID确保每次渲染的key绝对唯一
                    # 避免Streamlit检测到重复的element key
                    unique_key = f"del_{st.session_state.render_counter}_{trans['uuid']}_{idx}"
                    
                    # 删除按钮
                    if row_cols[6].button(
                        "Delete", 
                        key=unique_key, 
                        use_container_width=True
                    ):
                        # 删除本地记录
                        st.session_state.money_transfers = [
                            t for t in st.session_state.money_transfers 
                            if t["uuid"] != trans["uuid"]
                        ]
                        
                        # 同步到Google Sheets
                        if transfers_sheet and sheet_handler:
                            try:
                                cell = transfers_sheet.find(trans["uuid"])
                                if cell:
                                    transfers_sheet.delete_rows(cell.row)
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")
                        
                        st.success("Transaction deleted successfully!")
                        st.session_state.render_counter += 1  # 更新计数器确保下次渲染key变化
                        st.rerun()
        
        st.write("---")

    st.write("=" * 50)

    # 新增交易区域
    # 使用渲染计数器确保表单key唯一
    form_key = f"new_trans_{st.session_state.render_counter}"
    with st.form(key=form_key):
        st.subheader("Record New Transaction")
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input(
                "Transaction Date", 
                value=datetime.today(), 
                key=f"date_{st.session_state.render_counter}"
            )
            amount = st.number_input(
                "Amount ($)", 
                min_value=0.01, 
                step=0.01, 
                value=100.00, 
                key=f"amount_{st.session_state.render_counter}"
            )
            trans_type = st.radio(
                "Transaction Type", 
                ["Income", "Expense"], 
                index=0, 
                key=f"type_{st.session_state.render_counter}"
            )
        with col2:
            desc = st.text_input(
                "Description", 
                value="Fundraiser proceeds", 
                key=f"desc_{st.session_state.render_counter}"
            ).strip()
            handler = st.text_input(
                "Handled By", 
                value="Pikachu Da Best", 
                key=f"handler_{st.session_state.render_counter}"
            ).strip()

        submit = st.form_submit_button(
            "Record Transaction", 
            use_container_width=True, 
            type="primary"
        )

        if submit:
            if not (amount and desc and handler):
                st.error("Required fields: Amount, Description, Handled By!")
            else:
                new_trans = {
                    "uuid": str(uuid.uuid4()),
                    "Date": trans_date,
                    "Type": trans_type,
                    "Amount": round(amount, 2),
                    "Description": desc,
                    "Handler": handler
                }
                st.session_state.money_transfers.append(new_trans)
                
                if transfers_sheet and sheet_handler:
                    try:
                        transfers_sheet.append_row([
                            new_trans["uuid"],
                            new_trans["Date"].strftime("%Y-%m-%d"),
                            new_trans["Type"],
                            str(new_trans["Amount"]),
                            new_trans["Description"],
                            new_trans["Handler"]
                        ])
                    except Exception as e:
                        st.warning(f"同步失败: {str(e)}")
                
                st.success("Transaction recorded successfully!")
                st.session_state.render_counter += 1  # 更新计数器确保下次渲染key变化
                st.rerun()

render_money_transfers()
