import streamlit as st
from datetime import datetime
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 初始化Google Sheet连接
def init_google_sheet():
    # 配置认证范围
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    
    # 加载认证密钥（确保密钥文件在指定路径）
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "google_credentials.json",  # 替换为你的密钥文件路径
            scope
        )
        client = gspread.authorize(credentials)
        
        # 打开指定表格和工作表
        sheet = client.open("Student").worksheet("MoneyTransfer")
        
        # 检查并创建表头
        header = ["Date", "Amount ($)", "Category", "Description", "Handled By"]
        existing_header = sheet.row_values(1)
        if existing_header != header:
            sheet.clear()  # 清空现有内容
            sheet.append_row(header)  # 添加标准表头
            
        return sheet
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

    # 从Google Sheet加载数据
    def load_from_sheet():
        try:
            # 从第二行开始读取数据（跳过表头）
            records = sheet.get_all_records(start_row=2)
            st.session_state.money_transfers = []
            for idx, record in enumerate(records):
                try:
                    st.session_state.money_transfers.append({
                        "uuid": str(uuid.uuid4()),  # 本地生成UUID
                        "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                        "Type": "Income" if float(record["Amount ($)"]) >= 0 else "Expense",
                        "Amount": abs(float(record["Amount ($)"])),
                        "Description": record["Description"],
                        "Handler": record["Handled By"]
                    })
                except:
                    continue  # 跳过格式错误的行
        except Exception as e:
            st.warning(f"加载数据失败: {str(e)}")

    # 保存数据到Google Sheet
    def save_to_sheet():
        try:
            # 清除现有数据（保留表头）
            all_cells = sheet.range(2, 1, sheet.row_count, 5)
            for cell in all_cells:
                cell.value = ""
            sheet.update_cells(all_cells)
            
            # 写入新数据
            for trans in st.session_state.money_transfers:
                row_data = [
                    trans["Date"].strftime("%Y-%m-%d"),
                    trans["Amount"] if trans["Type"] == "Income" else -trans["Amount"],
                    "None",
                    trans["Description"],
                    trans["Handler"]
                ]
                sheet.append_row(row_data)
        except Exception as e:
            st.error(f"保存数据失败: {str(e)}")

    # 页面加载时从Sheet加载数据
    if "loaded" not in st.session_state:
        load_from_sheet()
        st.session_state.loaded = True

    # 处理删除操作
    if st.button("Delete Last Transaction", key="mt_del_last", use_container_width=True):
        if st.session_state.money_transfers:
            st.session_state.money_transfers.pop()
            save_to_sheet()  # 同步删除到Sheet
            st.success("Last transaction deleted successfully!")
            st.rerun()
        else:
            st.warning("No transactions to delete!")

    st.subheader("Transaction History")
        
    # 表格样式优化
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
        # 构建表格HTML
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

    # 新增交易区域
    st.subheader("Record New Transaction")
    cols = st.columns([15, 15, 10, 35, 25])
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
