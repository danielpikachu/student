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
    # 初始化Google Sheets连接
    sheet_handler = None
    transfers_sheet = None
    try:
        # 无需本地凭证路径，通过Streamlit Secrets获取认证
        sheet_handler = GoogleSheetHandler(credentials_path="")  # 路径参数仅为兼容，实际从secrets读取
        # 共用"Student"表格，使用"MoneyTransfers"工作表
        transfers_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="MoneyTransfers"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据到本地会话状态
    if transfers_sheet and ('money_transfers' not in st.session_state or not st.session_state.money_transfers):
        try:
            all_data = transfers_sheet.get_all_values()
            
            # 检查并创建表头（与calendar模块类似）
            if not all_data or all_data[0] != ["uuid", "date", "type", "amount", "description", "handler"]:
                transfers_sheet.clear()
                transfers_sheet.append_row(["uuid", "date", "type", "amount", "description", "handler"])
                records = []
            else:
                # 跳过表头，处理数据
                records = [
                    {
                        "uuid": row[0],
                        "Date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "Type": row[2],
                        "Amount": float(row[3]),
                        "Description": row[4],
                        "Handler": row[5]
                    } 
                    for row in all_data[1:] if row[0]  # 确保uuid存在
                ]
            
            st.session_state.money_transfers = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 修复：使用更独特的key，添加模块缩写+功能描述确保唯一性
    if st.button("Delete Last Transaction", key="student.modules.money_transfers.button.delete_last.202511051530.12345", use_container_width=True):
        if st.session_state.money_transfers:
            # 删除本地数据
            deleted = st.session_state.money_transfers.pop()
            # 同步删除Google Sheet数据
            if transfers_sheet and sheet_handler:
                try:
                    # 根据uuid查找并删除行
                    cell = transfers_sheet.find(deleted["uuid"])
                    if cell:
                        transfers_sheet.delete_rows(cell.row)
                except Exception as e:
                    st.warning(f"同步删除失败: {str(e)}")
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    # 显示交易历史
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet")
    else:
        table_data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            table_data.append({
                "No.": idx + 1,
                "Date": trans["Date"].strftime("%Y-%m-%d"),
                "Amount ($)": trans["Amount"],
                "Type": trans["Type"],
                "Description": trans["Description"],
                "Handled By": trans["Handler"]
            })
        st.dataframe(
            table_data,
            column_config={"Amount ($)": st.column_config.NumberColumn(format="$%.2f")},
            hide_index=True,
            use_container_width=True
        )

    st.write("=" * 50)

    # 新增交易区域
    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    with col1:
        # 为所有元素添加唯一key，使用mt_前缀+具体功能标识
        trans_date = st.date_input("Transaction Date", value=datetime.today(), key="mt_date_transaction")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, value=100.00, key="mt_num_amount")
        trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0, key="mt_radio_type")
    with col2:
        desc = st.text_input("Description", value="Fundraiser proceeds", key="mt_txt_description").strip()
        handler = st.text_input("Handled By", value="Pikachu Da Best", key="mt_txt_handler").strip()

    # 为记录按钮添加唯一key
    if st.button("Record Transaction", key="mt_btn_record_transaction", use_container_width=True, type="primary"):
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
            # 更新本地状态
            st.session_state.money_transfers.append(new_trans)
            # 同步到Google Sheet
            if transfers_sheet and sheet_handler:
                try:
                    # 写入数据（与表头字段对应）
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
