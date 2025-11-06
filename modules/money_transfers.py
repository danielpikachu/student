# modules/money_transfers.py
import streamlit as st
from datetime import datetime, timedelta
import uuid
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类（如果不需要可注释）
try:
    from google_sheet_utils import GoogleSheetHandler
except ImportError:
    GoogleSheetHandler = None
    st.warning("Google Sheets工具类未找到，将使用本地存储")

def render_money_transfers():
    """渲染转账模块界面（包含滚动条的交易历史表格）"""
    # 所有Streamlit命令必须放在函数内部
    st.header("💸 Money Transfers")
    st.markdown("---")

    # 添加自定义CSS样式（解决滚动条问题的核心样式）
    st.markdown("""
    <style>
        /* 滚动容器核心样式 - 确保优先级最高 */
        .scrollable-transactions {
            max-height: 250px !important;  /* 控制滚动触发的高度 */
            overflow-y: auto !important;   /* 强制垂直滚动 */
            padding: 10px !important;
            margin: 10px 0 !important;
            border: 1px solid #e0e0e0 !important;  /* 容器边框，方便观察范围 */
            border-radius: 4px !important;
        }

        /* 压缩表格内容高度 */
        .transaction-row {
            margin: 0 !important;
            padding: 2px 0 !important;
        }

        /* 缩小字体 */
        .small-text {
            font-size: 0.8rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }

        /* 压缩分隔线 */
        .transaction-separator {
            margin: 4px 0 !important;
            height: 1px !important;
            background-color: #f0f0f0 !important;
        }

        /* 优化按钮大小 */
        .stButton button {
            padding: 2px 8px !important;
            font-size: 0.7rem !important;
            height: auto !important;
        }

        /* 滚动条样式 */
        .scrollable-transactions::-webkit-scrollbar {
            width: 8px !important;
        }
        .scrollable-transactions::-webkit-scrollbar-track {
            background: #f5f5f5 !important;
            border-radius: 4px !important;
        }
        .scrollable-transactions::-webkit-scrollbar-thumb {
            background: #ccc !important;
            border-radius: 4px !important;
        }
        .scrollable-transactions::-webkit-scrollbar-thumb:hover {
            background: #aaa !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化本地存储的交易记录（如果没有Google Sheets）
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []
    
    # 初始化缓存和同步时间
    if "tra_cache_time" not in st.session_state:
        st.session_state.tra_cache_time = datetime.min
    if "tra_last_sync_time" not in st.session_state:
        st.session_state.tra_last_sync_time = datetime.min

    # Google Sheets连接（可选）
    sheet_handler = None
    transfers_sheet = None
    if GoogleSheetHandler:
        try:
            sheet_handler = GoogleSheetHandler(credentials_path="")
            transfers_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="MoneyTransfers"
            )
        except Exception as e:
            st.warning(f"Google Sheets连接提示: {str(e)}")

    # 同步数据（5分钟缓存）
    current_time = datetime.now()
    cache_valid = (current_time - st.session_state.tra_cache_time) < timedelta(minutes=5)
    need_sync = transfers_sheet and (not cache_valid or not st.session_state.tra_records)

    if need_sync and GoogleSheetHandler:
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
            st.session_state.tra_cache_time = current_time
            st.session_state.tra_last_sync_time = current_time
        except Exception as e:
            st.warning(f"数据同步失败，使用缓存: {str(e)}")

    # ---------------------- 交易历史展示（带滚动条） ----------------------
    st.subheader("Transaction History")
    if st.session_state.tra_last_sync_time != datetime.min:
        st.caption(f"Last synced: {st.session_state.tra_last_sync_time.strftime('%Y-%m-%d %H:%M')}")
    
    if not st.session_state.tra_records:
        st.info("No financial transactions recorded yet")
    else:
        # 滚动容器 - 确保正确包裹表格内容
        st.markdown('<div class="scrollable-transactions">', unsafe_allow_html=True)
        
        # 表头
        col_widths = [0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0]
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.markdown('<p class="small-text"><strong>#</strong></p>', unsafe_allow_html=True)
        with header_cols[1]:
            st.markdown('<p class="small-text"><strong>Date</strong></p>', unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown('<p class="small-text"><strong>Amount ($)</strong></p>', unsafe_allow_html=True)
        with header_cols[3]:
            st.markdown('<p class="small-text"><strong>Type</strong></p>', unsafe_allow_html=True)
        with header_cols[4]:
            st.markdown('<p class="small-text"><strong>Description</strong></p>', unsafe_allow_html=True)
        with header_cols[5]:
            st.markdown('<p class="small-text"><strong>Handled By</strong></p>', unsafe_allow_html=True)
        with header_cols[6]:
            st.markdown('<p class="small-text"><strong>Action</strong></p>', unsafe_allow_html=True)
        
        st.markdown('<hr class="transaction-separator">', unsafe_allow_html=True)
        
        # 交易记录行
        for idx, trans in enumerate(st.session_state.tra_records, 1):
            unique_key = f"tra_delete_{trans['uuid']}"
            cols = st.columns(col_widths)
            
            with cols[0]:
                st.markdown(f'<p class="small-text transaction-row">{idx}</p>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<p class="small-text transaction-row">{trans["date"].strftime("%Y-%m-%d")}</p>', unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f'<p class="small-text transaction-row">${trans["amount"]:.2f}</p>', unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f'<p class="small-text transaction-row">{trans["type"]}</p>', unsafe_allow_html=True)
            with cols[4]:
                st.markdown(f'<p class="small-text transaction-row">{trans["description"]}</p>', unsafe_allow_html=True)
            with cols[5]:
                st.markdown(f'<p class="small-text transaction-row">{trans["handler"]}</p>', unsafe_allow_html=True)
            with cols[6]:
                if st.button("🗑️", key=unique_key, use_container_width=True):
                    # 删除逻辑
                    st.session_state.tra_records = [t for t in st.session_state.tra_records if t["uuid"] != trans["uuid"]]
                    
                    # 同步到Google Sheets
                    if transfers_sheet and GoogleSheetHandler:
                        try:
                            cell = transfers_sheet.find(trans["uuid"])
                            if cell:
                                transfers_sheet.delete_rows(cell.row)
                            st.success(f"Transaction {idx} deleted")
                            st.session_state.tra_cache_time = datetime.min
                            st.rerun()
                        except Exception as e:
                            st.warning(f"删除同步失败: {str(e)}")
            
            st.markdown('<hr class="transaction-separator">', unsafe_allow_html=True)
        
        # 关闭滚动容器
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 汇总信息
        total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
        total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
        net_balance = total_income - total_expense
        
        st.markdown(f"""
        <div style='margin-top:1rem; padding:0.8rem; background:#f8f9fa; border-radius:4px'>
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
        trans_date = st.date_input("Transaction Date", datetime.today(), key="tra_date")
        amount = st.number_input("Amount ($)", 0.01, None, 100.00, 0.01, key="tra_amount")
        trans_type = st.radio("Type", ["Income", "Expense"], key="tra_type")
    
    with col2:
        description = st.text_input("Description", "Fundraiser", key="tra_desc").strip()
        handler = st.text_input("Handled By", "", key="tra_handler").strip()

    # 同步按钮
    if st.button("🔄 Sync Data", key="tra_sync") and transfers_sheet and GoogleSheetHandler:
        st.session_state.tra_cache_time = datetime.min
        st.success("Syncing...")
        st.rerun()

    # 记录交易按钮
    if st.button("Record Transaction", key="tra_record", use_container_width=True, type="primary"):
        if not description or not handler:
            st.error("Description and Handled By are required!")
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
        
        # 同步到Google Sheets
        if transfers_sheet and GoogleSheetHandler:
            try:
                transfers_sheet.append_row([
                    new_trans["uuid"],
                    new_trans["date"].strftime("%Y-%m-%d"),
                    new_trans["type"],
                    str(new_trans["amount"]),
                    new_trans["description"],
                    new_trans["handler"]
                ])
                st.success("Transaction recorded!")
                st.session_state.tra_cache_time = datetime.min
                st.rerun()
            except Exception as e:
                st.warning(f"同步失败: {str(e)}")
