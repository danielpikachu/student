# modules/money_transfers.py
import streamlit as st
from datetime import datetime
import uuid
import sys
import os

# 解决根目录导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 容错导入Google Sheets工具类
try:
    from google_sheet_utils import GoogleSheetHandler
except ImportError:
    GoogleSheetHandler = None

def render_money_transfers():
    st.header("💸 Money Transfers")
    st.markdown("---")

    # 核心CSS：仅作用于Transaction History和Summary之间的表格
    st.markdown("""
    <style>
        /* 滚动容器：明确位于Transaction History和Summary之间 */
        #transaction-table-container {
            max-height: 200px !important;  /* 控制滚动触发高度 */
            overflow-y: auto !important;   /* 内容溢出时显示滚动条 */
            border: 2px solid #ff4b4b !important;  /* 红色边框，确认范围 */
            padding: 10px !important;
            margin: 10px 0 !important;  /* 上下留出空间，与标题和汇总分隔 */
        }

        /* 表格内容压缩 */
        .table-row {
            font-size: 0.8rem !important;
            line-height: 1.2 !important;
            margin: 2px 0 !important;
        }

        /* 分隔线压缩 */
        .table-sep {
            margin: 3px 0 !important;
            height: 1px !important;
        }

        /* 滚动条样式 */
        #transaction-table-container::-webkit-scrollbar {
            width: 8px !important;
        }
        #transaction-table-container::-webkit-scrollbar-track {
            background: #f1f1f1 !important;
        }
        #transaction-table-container::-webkit-scrollbar-thumb {
            background: #888 !important;
            border-radius: 4px !important;
        }
        #transaction-table-container::-webkit-scrollbar-thumb:hover {
            background: #555 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化交易记录（默认11条数据用于测试）
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = [
            {
                "uuid": str(uuid.uuid4()),
                "date": datetime.now().date(),
                "type": "Income" if i % 2 == 0 else "Expense",
                "amount": 100.0 + i,
                "description": f"Transaction {i+1}",
                "handler": "User"
            } for i in range(11)  # 11条记录确保触发滚动
        ]

    # ---------------------- Transaction History 标题 ----------------------
    st.subheader("Transaction History")
    st.caption("Below is the transaction table with scrollbar")

    # ---------------------- 带滚动条的表格（核心区域） ----------------------
    # 红色边框容器：严格放在Transaction History标题和Summary之间
    st.markdown('<div id="transaction-table-container">', unsafe_allow_html=True)

    # 表格表头
    header_cols = st.columns([0.5, 1.5, 1.5, 1.5, 2.5, 1.5, 1.0])
    with header_cols[0]:
        st.markdown('<div class="table-row"><strong>#</strong></div>', unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown('<div class="table-row"><strong>Date</strong></div>', unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown('<div class="table-row"><strong>Amount ($)</strong></div>', unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown('<div class="table-row"><strong>Type</strong></div>', unsafe_allow_html=True)
    with header_cols[4]:
        st.markdown('<div class="table-row"><strong>Description</strong></div>', unsafe_allow_html=True)
    with header_cols[5]:
        st.markdown('<div class="table-row"><strong>Handled By</strong></div>', unsafe_allow_html=True)
    with header_cols[6]:
        st.markdown('<div class="table-row"><strong>Action</strong></div>', unsafe_allow_html=True)

    st.markdown('<hr class="table-sep">', unsafe_allow_html=True)

    # 表格内容行
    for idx, trans in enumerate(st.session_state.tra_records, 1):
        row_cols = st.columns([0.5, 1.5, 1.5, 1.5, 2.5, 1.5, 1.0])
        with row_cols[0]:
            st.markdown(f'<div class="table-row">{idx}</div>', unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f'<div class="table-row">{trans["date"].strftime("%Y-%m-%d")}</div>', unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f'<div class="table-row">${trans["amount"]:.2f}</div>', unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f'<div class="table-row">{trans["type"]}</div>', unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(f'<div class="table-row">{trans["description"]}</div>', unsafe_allow_html=True)
        with row_cols[5]:
            st.markdown(f'<div class="table-row">{trans["handler"]}</div>', unsafe_allow_html=True)
        with row_cols[6]:
            if st.button("🗑️", key=f"del_{trans['uuid']}", use_container_width=True):
                st.session_state.tra_records = [t for t in st.session_state.tra_records if t["uuid"] != trans["uuid"]]
                st.success(f"Deleted transaction {idx}")
                st.rerun()

        st.markdown('<hr class="table-sep">', unsafe_allow_html=True)

    # 关闭滚动容器（表格结束）
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- Summary 区域（在表格下方） ----------------------
    total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
    total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
    st.markdown(f"""
    <div style='margin-top:1rem; padding:10px; background:#f0f2f6; border-radius:4px'>
        <strong>Summary:</strong><br>
        Total Income: ${total_income:.2f} | 
        Total Expense: ${total_expense:.2f} | 
        Net Balance: ${(total_income - total_expense):.2f}
    </div>
    """, unsafe_allow_html=True)

    st.write("=" * 50)

    # ---------------------- 新增交易区域（不影响滚动表格） ----------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans"):
        col1, col2 = st.columns(2)
        with col1:
            trans_date = st.date_input("Date", datetime.today())
            amount = st.number_input("Amount ($)", 0.01, step=0.01)
            trans_type = st.radio("Type", ["Income", "Expense"])
        with col2:
            description = st.text_input("Description")
            handler = st.text_input("Handled By")
        if st.form_submit_button("Record", type="primary"):
            if description and handler:
                st.session_state.tra_records.append({
                    "uuid": str(uuid.uuid4()),
                    "date": trans_date,
                    "type": trans_type,
                    "amount": amount,
                    "description": description,
                    "handler": handler
                })
                st.success("Added successfully!")
                st.rerun()
            else:
                st.error("Please fill all fields")
