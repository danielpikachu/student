import streamlit as st
from datetime import datetime
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 自定义CSS样式
def add_custom_css():
    st.markdown("""
    <style>
    .transfer-record {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .transfer-header {
        font-weight: bold;
        color: #333;
        margin-bottom: 8px;
    }
    .transfer-amount {
        color: #2e7d32;
        font-weight: bold;
    }
    .negative-amount {
        color: #c62828;
    }
    </style>
    """, unsafe_allow_html=True)

def render_money_transfers():
    add_custom_css()
    st.header("💸 Money Transfer Records")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    transfer_sheet = None
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        sheet_handler = GoogleSheetHandler(credentials_path=creds_path)
        transfer_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="MoneyTransfer"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据到本地会话状态（从第二行开始读取）
    if transfer_sheet and ('transfer_records' not in st.session_state or not st.session_state.transfer_records):
        try:
            # 获取所有数据（包含表头）
            all_data = transfer_sheet.get_all_values()
            
            # 检查是否有表头，没有则创建表头
            if not all_data or all_data[0] != ["date", "amount", "description", "type"]:
                # 清除现有数据并设置表头
                transfer_sheet.clear()
                transfer_sheet.append_row(["date", "amount", "description", "type"])
                records = []
            else:
                # 跳过表头，处理从第二行开始的数据
                records = [
                    {
                        "Date": row[0],
                        "Amount": row[1],
                        "Description": row[2],
                        "Type": row[3]
                    } 
                    for row in all_data[1:] 
                    if row[0] and row[1] and row[3]  # 确保关键字段不为空
                ]
            
            # 转换为本地记录格式
            st.session_state.transfer_records = [
                {
                    "Date": datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                    "Amount": float(record["Amount"]),
                    "Description": record["Description"],
                    "Type": record["Type"]  # "in" 表示转入, "out" 表示转出
                } 
                for record in records 
            ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 显示交易记录
    if 'transfer_records' in st.session_state and st.session_state.transfer_records:
        # 按日期排序（最新的在前）
        sorted_records = sorted(
            st.session_state.transfer_records,
            key=lambda x: x["Date"],
            reverse=True
        )
        
        # 计算总余额
        total_balance = sum(
            record["Amount"] if record["Type"] == "in" else -record["Amount"]
            for record in sorted_records
        )
        
        st.metric("Current Balance", f"${total_balance:.2f}")
        st.divider()
        
        # 显示记录列表
        for record in sorted_records:
            amount_class = "transfer-amount" if record["Type"] == "in" else "transfer-amount negative-amount"
            amount_text = f"+${record['Amount']:.2f}" if record["Type"] == "in" else f"-${record['Amount']:.2f}"
            
            st.markdown(f"""
            <div class='transfer-record'>
                <div class='transfer-header'>
                    {record['Date'].strftime('%Y-%m-%d')} - {record['Type'].upper()}
                </div>
                <div class='{amount_class}'>{amount_text}</div>
                <div>{record['Description']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No transfer records found. Add your first transfer record below.")

    # 交易记录管理面板
    st.divider()
    with st.container(border=True):
        st.subheader("📝 Manage Transfer Records (Admin Only)")
        
        col_date, col_amount, col_type = st.columns(3)
        with col_date:
            selected_date = st.date_input(
                "Select Date",
                value=datetime.today(),
                label_visibility="collapsed"
            )
        
        with col_amount:
            transfer_amount = st.number_input(
                "Amount",
                min_value=0.01,
                step=0.01,
                format="%.2f",
                label_visibility="collapsed"
            )
        
        with col_type:
            transfer_type = st.selectbox(
                "Type",
                ["in", "out"],
                format_func=lambda x: "Income" if x == "in" else "Expense",
                label_visibility="collapsed"
            )
        
        transfer_desc = st.text_area(
            "Description (max 150 characters)",
            placeholder="Enter transfer details...",
            max_chars=150,
            label_visibility="collapsed"
        )
        
        col_save, col_delete = st.columns(2)
        with col_save:
            if st.button("💾 SAVE RECORD", use_container_width=True, type="primary", key="save_transfer"):
                if not transfer_desc.strip():
                    st.error("Description cannot be empty!")
                else:
                    if 'transfer_records' not in st.session_state:
                        st.session_state.transfer_records = []
                    
                    # 移除同日期同类型的旧记录（如果存在）
                    st.session_state.transfer_records = [
                        r for r in st.session_state.transfer_records 
                        if not (r["Date"] == selected_date and 
                                r["Type"] == transfer_type and 
                                r["Amount"] == transfer_amount)
                    ]
                    
                    # 添加新记录
                    st.session_state.transfer_records.append({
                        "Date": selected_date,
                        "Amount": transfer_amount,
                        "Description": transfer_desc.strip(),
                        "Type": transfer_type
                    })

                    if transfer_sheet and sheet_handler:
                        try:
                            # 删除同日期同类型的旧记录（从第二行开始搜索）
                            all_rows = transfer_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):  # 行索引从2开始（跳过表头）
                                if (row[0] == str(selected_date) and 
                                    row[1] == str(transfer_amount) and 
                                    row[3] == transfer_type):
                                    transfer_sheet.delete_rows(i)
                            
                            # 追加新记录
                            transfer_sheet.append_row([
                                str(selected_date),
                                str(transfer_amount),
                                transfer_desc.strip(),
                                transfer_type
                            ])
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")

                    st.success("✅ Record saved successfully!")
                    st.rerun()
        
        with col_delete:
            if st.button("🗑️ DELETE RECORD", use_container_width=True, key="delete_transfer"):
                if 'transfer_records' in st.session_state:
                    # 找到并删除选中的记录
                    deleted_count = 0
                    original_count = len(st.session_state.transfer_records)
                    
                    st.session_state.transfer_records = [
                        r for r in st.session_state.transfer_records 
                        if not (r["Date"] == selected_date and 
                                r["Type"] == transfer_type and 
                                r["Amount"] == transfer_amount)
                    ]
                    
                    deleted_count = original_count - len(st.session_state.transfer_records)
                    
                    if transfer_sheet and sheet_handler and deleted_count > 0:
                        try:
                            # 从第二行开始删除
                            all_rows = transfer_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if (row[0] == str(selected_date) and 
                                    row[1] == str(transfer_amount) and 
                                    row[3] == transfer_type):
                                    transfer_sheet.delete_rows(i)
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")

                    if deleted_count > 0:
                        st.success("✅ Record deleted successfully!")
                    else:
                        st.info("No matching record found to delete.")
                    st.rerun()

if __name__ == "__main__":
    render_money_transfer()
