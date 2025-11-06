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

# 导入Google Sheets工具类（容错处理）
try:
    from google_sheet_utils import GoogleSheetHandler
except ImportError:
    GoogleSheetHandler = None

def render_money_transfers():
    """渲染转账模块界面（强制滚动条版本）"""
    st.header("💸 Money Transfers")
    st.markdown("---")

    # 核心CSS - 强制滚动条显示，使用最高优先级
    st.markdown("""
    <style>
        /* 滚动容器 - 使用ID选择器确保最高优先级 */
        #transactions-container {
            max-height: 150px !important;  /* 关键：减小到150px确保11条记录溢出 */
            overflow-y: scroll !important;  /* 用scroll而不是auto，强制显示滚动条 */
            display: block !important;
            padding: 10px !important;
            margin: 10px 0 !important;
            border: 2px solid #ff4b4b !important;  /* 红色边框，明确看到容器范围 */
            box-sizing: border-box !important;
        }

        /* 彻底清除内部元素边距 */
        #transactions-container * {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.0 !important;
        }

        /* 最小化行高和字体 */
        .transaction-item {
            font-size: 0.7rem !important;
            padding: 2px 0 !important;
            min-height: auto !important;
        }

        /* 压缩分隔线 */
        .transaction-sep {
            margin: 2px 0 !important;
            height: 1px !important;
        }

        /* 强制滚动条始终可见 */
        #transactions-container::-webkit-scrollbar {
            width: 10px !important;
            display: block !important;
        }
        #transactions-container::-webkit-scrollbar-track {
            background: #ffebee !important;
        }
        #transactions-container::-webkit-scrollbar-thumb {
            background: #ff4b4b !important;
            border-radius: 5px !important;
        }

        /* 覆盖Streamlit默认容器样式 */
        .st-emotion-cache-1wivap2 {
            padding: 0 !important;
        }
        .st-emotion-cache-16txtl3 {
            padding: 0 !important;
            min-height: auto !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化交易记录
    if "tra_records" not in st.session_state:
        # 预填11条测试数据（方便测试滚动条）
        st.session_state.tra_records = [
            {
                "uuid": str(uuid.uuid4()),
                "date": datetime.now().date(),
                "type": "Income" if i % 2 == 0 else "Expense",
                "amount": 100.0 + i,
                "description": f"Test transaction {i}",
                "handler": "Test User"
            } for i in range(11)
        ]
    
    # 初始化缓存时间
    if "tra_cache_time" not in st.session_state:
        st.session_state.tra_cache_time = datetime.min
    if "tra_last_sync_time" not in st.session_state:
        st.session_state.tra_last_sync_time = datetime.min

    # Google Sheets连接（保持原有逻辑）
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

    # ---------------------- 交易历史展示（强制滚动条） ----------------------
    st.subheader("Transaction History")
    
    # 用ID选择器的容器包裹表格（最高优先级）
    st.markdown('<div id="transactions-container">', unsafe_allow_html=True)
    
    # 表头
    cols = st.columns([0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0])
    with cols[0]:
        st.markdown('<div class="transaction-item"><strong>#</strong></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown('<div class="transaction-item"><strong>Date</strong></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="transaction-item"><strong>Amount</strong></div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown('<div class="transaction-item"><strong>Type</strong></div>', unsafe_allow_html=True)
    with cols[4]:
        st.markdown('<div class="transaction-item"><strong>Description</strong></div>', unsafe_allow_html=True)
    with cols[5]:
        st.markdown('<div class="transaction-item"><strong>Handled By</strong></div>', unsafe_allow_html=True)
    with cols[6]:
        st.markdown('<div class="transaction-item"><strong>Action</strong></div>', unsafe_allow_html=True)
    
    st.markdown('<hr class="transaction-sep">', unsafe_allow_html=True)
    
    # 交易记录
    for idx, trans in enumerate(st.session_state.tra_records, 1):
        unique_key = f"del_{trans['uuid']}"
        cols = st.columns([0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0])
        
        with cols[0]:
            st.markdown(f'<div class="transaction-item">{idx}</div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f'<div class="transaction-item">{trans["date"].strftime("%Y-%m-%d")}</div>', unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f'<div class="transaction-item">${trans["amount"]:.2f}</div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f'<div class="transaction-item">{trans["type"]}</div>', unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f'<div class="transaction-item">{trans["description"]}</div>', unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f'<div class="transaction-item">{trans["handler"]}</div>', unsafe_allow_html=True)
        with cols[6]:
            if st.button("🗑️", key=unique_key, use_container_width=True):
                st.session_state.tra_records = [t for t in st.session_state.tra_records if t["uuid"] != trans["uuid"]]
                st.success(f"Deleted transaction {idx}")
                st.rerun()
        
        st.markdown('<hr class="transaction-sep">', unsafe_allow_html=True)
    
    # 关闭容器
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 汇总信息
    total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
    total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
    st.markdown(f"""
    <div style='margin-top:1rem'>
        <strong>Summary:</strong> Income: ${total_income:.2f} | Expense: ${total_expense:.2f} | 
        Balance: ${(total_income - total_expense):.2f}
    </div>
    """, unsafe_allow_html=True)

    st.write("=" * 50)

    # ---------------------- 新增交易区域 ----------------------
    st.subheader("Record New Transaction")
    with st.form("new_transaction"):
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("Date", datetime.today())
            amount = st.number_input("Amount ($)", 0.01, step=0.01)
            trans_type = st.radio("Type", ["Income", "Expense"])
        
        with col2:
            description = st.text_input("Description")
            handler = st.text_input("Handled By")
        
        submitted = st.form_submit_button("Record Transaction", type="primary")
        if submitted:
            if not description or not handler:
                st.error("Please fill all fields")
            else:
                st.session_state.tra_records.append({
                    "uuid": str(uuid.uuid4()),
                    "date": trans_date,
                    "type": trans_type,
                    "amount": amount,
                    "description": description,
                    "handler": handler
                })
                st.success("Transaction recorded!")
                st.rerun()
