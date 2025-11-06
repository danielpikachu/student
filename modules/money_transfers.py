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

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_money_transfers():
    """渲染转账模块界面（tra_前缀命名空间）"""
    st.header("💸 Money Transfers")
    st.markdown("---")

    # 添加自定义CSS样式优化表格显示（新增滚动容器样式）
    st.markdown("""
    <style>
        /* 缩小行间距和整体高度 */
        .st-emotion-cache-16txtl3 {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
        }
        .st-emotion-cache-1v0mbdj {
            min-height: 0.3rem !important;
        }
        .stMarkdown {
            margin: 0 !important;
        }
        /* 缩小分隔线间距和高度 */
        hr {
            margin: 0.1rem 0 !important;
            height: 1px !important;
        }
        /* 缩小字体大小 */
        .small-text {
            font-size: 0.8rem !important;
            margin: 0 !important;
        }
        /* 紧凑按钮样式 */
        .stButton button {
            padding: 0.2rem 0.4rem !important;
            font-size: 0.75rem !important;
        }
        /* 滚动容器样式（关键修改） */
        .scrollable-container {
            max-height: 50px;  /* 减小最大高度（原400px），7条数据更易触发滚动 */
            overflow-y: auto;   /* 垂直溢出时显示滚动条 */
            padding-right: 10px; /* 预留滚动条空间，避免内容被遮挡 */
            margin-bottom: 1rem; /* 与下方汇总信息分隔 */
        }
        /* 优化滚动条外观 */
        .scrollable-container::-webkit-scrollbar {
            width: 6px;
        }
        .scrollable-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        .scrollable-container::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        .scrollable-container::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化缓存相关状态
    if "tra_cache_time" not in st.session_state:
        st.session_state.tra_cache_time = datetime.min
    if "tra_last_sync_time" not in st.session_state:
        st.session_state.tra_last_sync_time = datetime.min

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
        st.warning(f"Google Sheets 连接提示: {str(e)}")  # 改为警告不阻断流程

    # 从Google Sheets同步数据（使用缓存机制避免频繁请求）
    current_time = datetime.now()
    cache_valid = (current_time - st.session_state.tra_cache_time) < timedelta(minutes=5)
    need_sync = transfers_sheet and sheet_handler and (not cache_valid or not st.session_state.get("tra_records"))

    if need_sync:
        try:
            all_data = transfers_sheet.get_all_values()
            expected_headers = ["uuid", "date", "type", "amount", "description", "handler"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                transfers_sheet.clear()
                transfers_sheet.append_row(expected_headers)
                records = []
            else:
                # 处理数据（跳过表头）
                records = [
                    {
                        "uuid": row[0],
                        "date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "type": row[2],
                        "amount": float(row[3]),
                        "description": row[4],
                        "handler": row[5]
                    } 
                    for row in all_data[1:] 
                    if row[0]  # 确保UUID不为空
                ]
            
            st.session_state.tra_records = records
            st.session_state.tra_cache_time = current_time  # 更新缓存时间
            st.session_state.tra_last_sync_time = current_time
        except Exception as e:
            st.warning(f"数据同步失败，使用缓存数据: {str(e)}")

    # 初始化状态（防止首次加载时出错）
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []

    # ---------------------- 交易历史展示（带滚动条） ----------------------
    st.subheader("Transaction History")
    # 显示最后同步时间
    if st.session_state.tra_last_sync_time != datetime.min:
        st.caption(f"Last synced: {st.session_state.tra_last_sync_time.strftime('%Y-%m-%d %H:%M')}")
    
    if not st.session_state.tra_records:
        st.info("No financial transactions recorded yet")
    else:
        # 用滚动容器包裹表格内容
        st.markdown('<div class="scrollable-container">', unsafe_allow_html=True)
        
        # 定义列宽比例
        col_widths = [0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0]
        
        # 显示表头（应用紧凑样式）
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
        
        st.markdown("---")  # 表头分隔线
        
        # 遍历显示每笔交易
        for idx, trans in enumerate(st.session_state.tra_records, 1):
            unique_key = f"tra_delete_{idx}_{trans['uuid']}"
            cols = st.columns(col_widths)
            
            # 填充交易数据（应用紧凑样式）
            with cols[0]:
                st.markdown(f'<p class="small-text">{idx}</p>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<p class="small-text">{trans["date"].strftime("%Y-%m-%d")}</p>', unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f'<p class="small-text">${trans["amount"]:.2f}</p>', unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f'<p class="small-text">{trans["type"]}</p>', unsafe_allow_html=True)
            with cols[4]:
                st.markdown(f'<p class="small-text">{trans["description"]}</p>', unsafe_allow_html=True)
            with cols[5]:
                st.markdown(f'<p class="small-text">{trans["handler"]}</p>', unsafe_allow_html=True)
            with cols[6]:
                # 删除按钮
                if st.button(
                    "🗑️ Delete", 
                    key=unique_key,
                    use_container_width=True,
                    type="secondary"
                ):
                    # 从本地状态删除
                    st.session_state.tra_records.pop(idx - 1)
                    
                    # 同步删除Google Sheets记录
                    if transfers_sheet and sheet_handler:
                        try:
                            cell = transfers_sheet.find(trans["uuid"])
                            if cell:
                                transfers_sheet.delete_rows(cell.row)
                            st.success(f"Transaction {idx} deleted successfully!")
                            st.session_state.tra_cache_time = datetime.min  # 强制下次同步
                            st.rerun()
                        except Exception as e:
                            st.warning(f"同步删除失败: {str(e)}")
            
            st.markdown("---")  # 行分隔线
        
        # 关闭滚动容器
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 显示汇总信息
        total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
        total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
        net_balance = total_income - total_expense
        
        st.markdown(f"""
        <div style='margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;'>
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

    # 手动同步按钮（供用户主动刷新数据）
    col_sync, _ = st.columns([1, 5])
    with col_sync:
        if st.button("🔄 Sync Data", key="tra_btn_sync") and transfers_sheet and sheet_handler:
            st.session_state.tra_cache_time = datetime.min  # 强制同步
            st.success("Syncing data...")
            st.rerun()

    # 记录交易按钮
    if st.button("Record Transaction", key="tra_btn_record", use_container_width=True, type="primary"):
        # 验证必填字段
        if not description or not handler:
            st.error("Description and Handled By are required fields!")
            return
        
        # 创建新交易记录
        new_trans = {
            "uuid": str(uuid.uuid4()),  # 生成唯一标识
            "date": trans_date,
            "type": trans_type,
            "amount": round(amount, 2),
            "description": description,
            "handler": handler
        }
        
        # 更新本地状态
        st.session_state.tra_records.append(new_trans)
        
        # 同步到Google Sheets
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
                st.success("Transaction recorded successfully!")
                st.session_state.tra_cache_time = datetime.min  # 强制下次同步
                st.rerun()
            except Exception as e:
                st.warning(f"同步到Google Sheets失败: {str(e)}")
