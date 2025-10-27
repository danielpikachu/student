import streamlit as st
import pandas as pd
from datetime import date

def render_money(is_admin):
    """资金模块：管理收支记录"""
    st.subheader("💸 资金管理")
    st.write("记录和查看学生会收支明细")
    st.divider()
    
    # 显示交易记录
    st.subheader("交易记录")
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False).reset_index(drop=True)
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn("日期"),
                "amount": st.column_config.NumberColumn("金额（元）", format="%.2f"),
                "desc": "描述",
                "handler": "经手人"
            },
            hide_index=True
        )
        
        # 财务汇总
        income = sum(t["amount"] for t in st.session_state.transactions if t["amount"] > 0)
        expense = sum(t["amount"] for t in st.session_state.transactions if t["amount"] < 0)
        balance = income + expense
        
        col1, col2, col3 = st.columns(3)
        col1.metric("总收入", f"¥{income:.2f}")
        col2.metric("总支出", f"¥{expense:.2f}")
        col3.metric("当前余额", f"¥{balance:.2f}")
    else:
        st.info("暂无交易记录")
    
    # 管理员操作
    if is_admin:
        with st.expander("🔧 新增交易", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("金额（元）", value=100.0, step=10.0)
                is_expense = st.checkbox("标记为支出（自动转为负数）")
                if is_expense:
                    amount = -abs(amount)
            
            with col2:
                trans_date = st.date_input("交易日期", date.today())
                desc = st.text_input("交易描述", "例如：赞助、采购")
            
            handler = st.text_input("经手人", st.session_state.user)
            
            if st.button("记录交易"):
                if not desc.strip():
                    st.error("请输入交易描述")
                    return
                st.session_state.transactions.append({
                    "date": trans_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "desc": desc,
                    "handler": handler
                })
                st.success("交易已记录")
