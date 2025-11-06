# modules/moneyoney_transfers.py
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
    """渲染转账模块界面（带紧凑行距和滚动条）"""
    st.header("💸 Money Transfers")
    st.markdown("---")

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

    # 从Google Sheets同步数据
    if transfers_sheet and sheet_handler and (not st.session_state.get("tra_records")):
        try:
            all_data = transfers_sheet.get_all_values()
            expected_headers = ["uuid", "date", "type", "amount", "description", "handler"]
            
            if not all_data or all_data[0] != expected_headers:
                transfers_sheet.clear()
                transfers_sheet.append_row(expected_headers)
                records = []
            else:
                records = [
                    {
                        "uuid": row[0],
                        "date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "type": row[2],
                        "amount": float(row[3]),
                        "description": row[4],
                        "handler": row[5]
                    } 
                    for row in all_data[1:] if row[0]
                ]
            
            st.session_state.tra_records = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 初始化状态
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []

    # ---------------------- 强制生效的CSS样式 ----------------------
    st.markdown("""
    <style>
        /* 滚动容器 - 直接作用于streamlit的容器元素 */
        [data-testid="stVerticalBlock"] > div:nth-child(3) > div {
            max-height: 300px !important;
            overflow-y: auto !important;
            padding: 10px !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 5px !important;
        }
        
        /* 缩小所有行元素的间距 */
        [data-testid="stVerticalBlock"] > div:nth-child(3) .stMarkdown,
        [data-testid="stVerticalBlock"] > div:nth-child(3) .stButton {
            margin-top: 2px !important;
            margin-bottom: 2px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* 缩小分隔线 */
        [data-testid="stVerticalBlock"] > div:nth-child(3) hr {
            margin: 4px 0 !important;
            height: 1px !important;
            background-color: #f0f0f0 !important;
        }
        
        /* 紧凑按钮样式 */
        [data-testid="stVerticalBlock"] > div:nth-child(3) .stButton button {
            padding: 2px 8px !important;
            font-size: 12px !important;
            height: 28px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ---------------------- 交易历史展示（带滚动条） ----------------------
    st.subheader("Transaction History")
    
    # 这是第3个垂直块容器（用于CSS定位）
    with st.container():
        if not st.session_state.tra_records:
            st.info("No financial transactions recorded yet")
        else:
            # 列宽比例
            col_widths = [0.2, 1.0, 1.0, 1.0, 2.2, 1.3, 0.7]
            
            # 表头
            header_cols = st.columns(col_widths)
            with header_cols[0]:
                st.write("**#**")
            with header_cols[1]:
                st.write("**Date**")
            with header_cols[2]:
                st.write("**Amount**")
            with header_cols[3]:
                st.write("**Type**")
            with header_cols[4]:
                st.write("**Description**")
            with header_cols[5]:
                st.write("**Handled By**")
            with header_cols[6]:
                st.write("**Del**")
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # 遍历交易记录
            for idx, trans in enumerate(st.session_state.tra_records, 1):
                unique_key = f"tra_del_{trans['uuid']}"
                
                cols = st.columns(col_widths)
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(trans["date"].strftime("%Y-%m-%d"))
                with cols[2]:
                    st.write(f"${trans['amount']:.2f}")
                with cols[3]:
                    st.write(trans["type"])
                with cols[4]:
                    st.write(trans["description"])
                with cols[5]:
                    st.write(trans["handler"])
                with cols[6]:
                    if st.button("🗑️", key=unique_key, use_container_width=True):
                        # 本地删除
                        st.session_state.tra_records = [t for t in st.session_state.tra_records if t["uuid"] != trans["uuid"]]
                        
                        # 同步删除
                        if transfers_sheet and sheet_handler:
                            try:
                                cell = transfers_sheet.find(trans["uuid"])
                                if cell:
                                    transfers_sheet.delete_rows(cell.row)
                                st.success("Deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"同步失败: {str(e)}")
            
                st.markdown("<hr>", unsafe_allow_html=True)

    # 汇总信息
    if st.session_state.tra_records:
        total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
        total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
        net_balance = total_income - total_expense
        
        st.markdown(f"""
        <div style='padding: 0.8rem; background-color: #f8f9fa; border-radius: 6px;'>
            <strong>Summary:</strong><br>
            Total Income: ${total_income:.2f} | 
            Total Expense: ${total_expense:.2f} | 
            Net Balance: ${net_balance:.2f}
        </div>
        """, unsafe_allow_html=True)

    st.write("=" * 50)

    # ---------------------- 新增交易 ----------------------
    st.subheader("Record New Transaction")
    col1, col2 = st.columns(2)
    
    with col1:
        trans_date = st.date_input(
            "Transaction Date", 
            value=datetime.today(),
            key="tra_input_date"
        )
        
        amount = st.number_input(
            "Amount ($)", 
            min_value=0.01, 
            step=0.01, 
            value=100.00,
            key="tra_input_amount"
        )
        
        trans_type = st.radio(
            "Transaction Type", 
            ["Income", "Expense"], 
            index=0,
            key="tra_radio_type"
        )
    
    with col2:
        description = st.text_input(
            "Description", 
            value="Fundraiser proceeds",
            key="tra_input_desc"
        ).strip()
        
        handler = st.text_input(
            "Handled By", 
            value="",
            key="tra_input_handler"
        ).strip()

    if st.button("Record Transaction", key="tra_btn_record", use_container_width=True, type="primary"):
        if not description or not handler:
            st.error("Description and Handled By are required fields!")
            return
        
        new_trans = {
            "uuid": str(uuid.uuid4()),
            "date": trans_date,
            "type": trans_type,
            "amount": round(amount, 2),
            "description": description,
            "handler": handler
        }
        
        st.session_state.tra_records.append(new_trans)
        
        if transfers_sheet and sheet_handler:
            try:
                transfers_sheet.append_row([
                    new_trans["uuid"],
                    new_trans["date"].strftime("%Y-%m-%d"),
                    new_trans["type"],
                    str(new_trans["amount"]),
                    new_trans["description"],
                    new_trans["handler"]
                ])
                st.success("Recorded successfully!")
                st.rerun()
            except Exception as e:
                st.warning(f"同步失败: {str(e)}")
