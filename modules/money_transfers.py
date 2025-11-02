import streamlit as st
from datetime import datetime
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# 初始化Google Sheet连接（适配Streamlit Cloud密钥管理）
def init_google_sheet():
    # 从Streamlit Cloud密钥获取认证信息
    try:
        # 从st.secrets加载Google认证信息
        credentials_dict = st.secrets["GOOGLE_SHEETS_CREDENTIALS"]
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # 使用字典创建认证对象（无需本地JSON文件）
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict,
            scope
        )
        client = gspread.authorize(credentials)
        
        # 打开指定表格和工作表
        sheet = client.open("Student").worksheet("MoneyTransfer")
        
        # 检查并创建表头（第一行）
        header = ["Date", "Amount ($)", "Category", "Description", "Handled By"]
        existing_header = sheet.row_values(1)
        if existing_header != header:
            sheet.clear()  # 清空现有内容
            sheet.append_row(header)  # 添加标准表头
            
        return sheet
    except KeyError:
        st.error("请在Streamlit Cloud中配置'GOOGLE_SHEETS_CREDENTIALS'密钥")
        return None
    except Exception as e:
        st.error(f"Google Sheet连接失败: {str(e)}")
        return None

def render_money_transfers():
    # 初始化状态
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []
    
    # 初始化Google Sheet连接
    sheet = init_google_sheet()
    if not sheet:
        return

    st.header("Financial Transactions")
    st.write("=" * 50)

    # 从Google Sheet加载数据（从第二行开始）
    def load_from_sheet():
        try:
            # 从第二行读取所有记录（跳过表头）
            records = sheet.get_all_records(start_row=2)
            st.session_state.money_transfers = []
            for record in records:
                try:
                    # 解析金额和类型（正数为收入，负数为支出）
                    amount = float(record["Amount ($)"])
                    trans_type = "Income" if amount >= 0 else "Expense"
                    
                    st.session_state.money_transfers.append({
                        "uuid": str(uuid.uuid4()),
                        "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                        "Type": trans_type,
                        "Amount": abs(amount),  # 存储绝对值，用Type区分正负
                        "Description": record["Description"],
                        "Handler": record["Handled By"]
                    })
                except Exception as e:
                    st.warning(f"跳过格式错误的行: {str(e)}")
                    continue
        except Exception as e:
            st.warning(f"加载数据失败: {str(e)}")

    # 保存数据到Google Sheet（从第二行开始写入）
    def save_to_sheet():
        try:
            # 清除现有数据（保留表头，从第二行开始清空）
            if sheet.row_count > 1:
                sheet.delete_rows(2, sheet.row_count)
            
            # 写入所有数据（从第二行开始）
            for trans in st.session_state.money_transfers:
                # 收入为正数，支出为负数
                amount = trans["Amount"] if trans["Type"] == "Income" else -trans["Amount"]
                row_data = [
                    trans["Date"].strftime("%Y-%m-%d"),
                    round(amount, 2),
                    "None",  # 类别暂为None
                    trans["Description"],
                    trans["Handler"]
                ]
                sheet.append_row(row_data)
        except Exception as e:
            st.error(f"保存数据失败: {str(e)}")

    # 页面首次加载时从Sheet加载数据
    if "loaded" not in st.session_state:
        load_from_sheet()
        st.session_state.loaded = True

    # 处理删除操作（删除最后一行并同步到Sheet）
    if st.button("Delete Last Transaction", key="mt_del_last", use_container_width=True):
        if st.session_state.money_transfers:
            st.session_state.money_transfers.pop()
            save_to_sheet()  # 同步删除到Google Sheet
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    st.subheader("Transaction History")
        
    # 表格样式（保持列对齐）
    st.markdown("""
    <style>
    .transaction-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .transaction-table td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    .column-names {
        background-color: #e8f4f8;
        font-weight: 600;
    }
    .amount-col {
        text-align: right !important;
        width: 15%;
    }
    .date-col { width: 15%; }
    .category-col { width: 10%; }
    .description-col { width: 35%; }
    .handler-col { width: 25%; }
    .income { color: green; }
    .expense { color: red; }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.money_transfers:
        st.info("No transactions recorded yet")
    else:
        # 构建表格HTML（第一行为表头，后续为数据）
        table_html = """
        <table class="transaction-table">
            <tbody>
                <tr class="column-names">
                    <td class="date-col">Date</td>
                    <td class="amount-col">Amount ($)</td>
                    <td class="category-col">Category</td>
                    <td class="description-col">Description</td>
                    <td class="handler-col">Handled By</td>
                </tr>
        """
        
        # 添加数据行
        for trans in st.session_state.money_transfers:
            table_html += f"""
            <tr>
                <td class="date-col">{trans['Date'].strftime('%Y-%m-%d')}</td>
                <td class="amount-col { 'income' if trans['Type'] == 'Income' else 'expense' }">
                    ${trans['Amount']:.2f}
                </td>
                <td class="category-col">None</td>
                <td class="description-col">{trans['Description']}</td>
                <td class="handler-col">{trans['Handler']}</td>
            </tr>
            """
        
        table_html += """
            </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    st.write("=" * 50)

    # 新增交易区域（与表格列对应）
    st.subheader("Record New Transaction")
    cols = st.columns([15, 15, 10, 35, 25])  # 与表格列宽比例一致
    with cols[0]:
        trans_date = st.date_input("Date", datetime.today(), key="mt_date")
    with cols[1]:
        amount = st.number_input("Amount ($)", 0.01, step=0.01, key="mt_amount")
    with cols[2]:
        trans_type = st.radio("Type", ["Income", "Expense"], key="mt_type", horizontal=True)
    with cols[3]:
        desc = st.text_input("Description", key="mt_desc").strip()
    with cols[4]:
        handler = st.text_input("Handled By", key="mt_handler").strip()

    if st.button("Record Transaction", key="mt_add", use_container_width=True, type="primary"):
        if not (amount and desc and handler):
            st.error("Please fill in all required fields!")
        else:
            # 添加到本地状态
            st.session_state.money_transfers.append({
                "uuid": str(uuid.uuid4()),
                "Date": trans_date,
                "Type": trans_type,
                "Amount": round(amount, 2),
                "Description": desc,
                "Handler": handler
            })
            # 同步到Google Sheet
            save_to_sheet()
            st.success("Transaction recorded and synced to Google Sheet!")
            st.rerun()

render_money_transfers()
