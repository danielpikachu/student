import streamlit as st
from datetime import datetime
import uuid
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_money_transfers():
    # 初始化会话状态（确保money_transfers存在）
    if 'money_transfers' not in st.session_state:
        st.session_state.money_transfers = []
    
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
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据到本地会话状态（仅在本地为空时同步）
    if transfers_sheet and not st.session_state.money_transfers:
        try:
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
                    for row in all_data[1:] if row[0]
                ]
            
            st.session_state.money_transfers = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 显示交易历史（带每条记录的删除按钮）
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        # 使用容器包裹表格，避免渲染冲突
        with st.container():
            # 显示表头
            cols = st.columns([0.5, 1.5, 1.5, 1.2, 2, 1.5, 1.2])
            headers = ["No.", "Date", "Amount ($)", "Type", "Description", "Handled By", "Action"]
            for col, header in zip(cols, headers):
                col.write(f"**{header}**")
            
            # 显示每条交易记录及删除按钮
            # 复制列表避免迭代时修改导致的问题
            for idx, trans in enumerate(list(st.session_state.money_transfers)):
                row_cols = st.columns([0.5, 1.5, 1.5, 1.2, 2, 1.5, 1.2])
                
                # 显示交易数据
                row_cols[0].write(idx + 1)
                row_cols[1].write(trans["Date"].strftime("%Y-%m-%d"))
                row_cols[2].write(f"${trans['Amount']:.2f}")
                row_cols[3].write(trans["Type"])
                row_cols[4].write(trans["Description"])
                row_cols[5].write(trans["Handler"])
                
                # 仅使用记录自身的uuid作为唯一key（最可靠的方式）
                unique_key = f"delete_{trans['uuid']}"
                
                # 删除按钮
                if row_cols[6].button(
                    "Delete", 
                    key=unique_key, 
                    use_container_width=True
                ):
                    # 通过uuid删除记录（避免索引变化导致的错误）
                    st.session_state.money_transfers = [
                        t for t in st.session_state.money_transfers 
                        if t["uuid"] != trans["uuid"]
                    ]
                    # 同步删除Google Sheet数据
                    if transfers_sheet and sheet_handler:
                        try:
                            cell = transfers_sheet.find(trans["uuid"])
                            if cell:
                                transfers_sheet.delete_rows(cell.row)
                        except Exception as e:
                            st.warning(f"同步删除失败: {str(e)}")
                    st.success("Transaction deleted successfully!")
                    st.rerun()
        
        st.write("---")

    st.write("=" * 50)

    # 新增交易区域
    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        # 为输入组件添加唯一后缀，避免与其他模块冲突
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="mt_date_uniq")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, value=100.00, key="mt_amount_uniq")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key="mt_type_uniq")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key="mt_desc_uniq").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key="mt_handler_uniq").strip()

    if st.button("Record Transaction", key="mt_record_uniq", use_container_width=True, type="primary"):
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
                    st.warning(f"同步到Google Sheets失败: {str(e)}")
            st.success("Transaction recorded successfully!")
            st.rerun()

render_money_transfers()
