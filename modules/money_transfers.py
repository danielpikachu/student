# modules/money_transfers.py
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
    """渲染转账模块界面（tra_前缀命名空间）"""
    st.header("💸 Money Transfers")
    st.markdown("---")

    # 添加强制滚动条样式
    st.markdown("""
    <style>
        .fixed-height-scroll {
            height: 400px;  /* 固定高度，确保超过时出现滚动条 */
            overflow-y: scroll;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        /* 移除Streamlit默认的内部边距干扰 */
        .stBlockContainer {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 初始化状态
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []

    # 模拟数据（测试用，可删除）
    if not st.session_state.tra_records:
        for i in range(7):  # 确保有7条测试数据
            st.session_state.tra_records.append({
                "uuid": str(uuid.uuid4()),
                "date": datetime.now().date(),
                "type": "Income" if i % 2 == 0 else "Expense",
                "amount": 100.0 + i,
                "description": f"Test transaction {i+1}",
                "handler": "Test User"
            })

    # ---------------------- 交易历史展示（强制滚动条） ----------------------
    st.subheader("Transaction History")
    
    # 使用HTML容器强制固定高度
    st.markdown('<div class="fixed-height-scroll">', unsafe_allow_html=True)
    
    # 定义列宽
    col_widths = [0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0]
    
    # 表头
    header_cols = st.columns(col_widths)
    header_cols[0].write("**#**")
    header_cols[1].write("**Date**")
    header_cols[2].write("**Amount ($)**")
    header_cols[3].write("**Type**")
    header_cols[4].write("**Description**")
    header_cols[5].write("**Handled By**")
    header_cols[6].write("**Action**")
    
    st.markdown("---")
    
    # 表格内容
    for idx, trans in enumerate(st.session_state.tra_records, 1):
        unique_key = f"del_{idx}_{trans['uuid']}"
        cols = st.columns(col_widths)
        
        cols[0].write(idx)
        cols[1].write(trans["date"].strftime("%Y-%m-%d"))
        cols[2].write(f"${trans['amount']:.2f}")
        cols[3].write(trans["type"])
        cols[4].write(trans["description"])
        cols[5].write(trans["handler"])
        
        if cols[6].button("🗑️", key=unique_key, use_container_width=True):
            st.session_state.tra_records.pop(idx-1)
            st.rerun()
        
        st.markdown("---")
    
    # 关闭滚动容器
    st.markdown('</div>', unsafe_allow_html=True)

    # 汇总信息
    total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
    total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
    st.info(f"Total: Income ${total_income:.2f} | Expense ${total_expense:.2f} | Balance ${total_income-total_expense:.2f}")

    # 新增交易部分（保持不变）
    st.subheader("Record New Transaction")
    # ...（此处省略新增交易代码，保持原样）
