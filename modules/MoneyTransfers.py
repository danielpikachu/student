import streamlit as st
import pandas as pd
from datetime import date, datetime
import uuid

def render_money_transfers(is_admin):
    st.subheader("💸 资金交易管理")
    st.write("记录和查看学生会财务交易")
    st.divider()

    # 确保交易记录有唯一ID
    if st.session_state.transactions:
        for t in st.session_state.transactions:
            if "id" not in t:
                t["id"] = str(uuid.uuid4())

    # 显示交易记录
    st.subheader("交易历史")
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False).reset_index(drop=True)

        # 筛选功能
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            date_range = st.date_input(
                "筛选日期范围",
                value=[df["date"].min().date(), df["date"].max().date()],
                min_value=df["date"].min().date(),
                max_value=df["date"].max().date()
            )
        with col_filter2:
            trans_type = st.selectbox("筛选交易类型", ["全部", "收入", "支出"])

        # 应用筛选
        mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
        if trans_type == "收入":
            mask &= df["amount"] > 0
        elif trans_type == "支出":
            mask &= df["amount"] < 0
        filtered_df = df[mask]

        # 显示表格
        st.dataframe(
            filtered_df.drop(columns=["id"]),
            use_container_width=True,
            column_config={
                "date": st.column_config.DateColumn("日期"),
                "amount": st.column_config.NumberColumn(
                    "金额 (¥)",
                    format="¥%.2f",
                    cell_style=lambda x: {"color": "green" if x > 0 else "red"}
                ),
                "desc": "描述",
                "handler": "经手人"
            },
            hide_index=True
        )

        # 财务汇总
        income = sum(filtered_df[filtered_df["amount"] > 0]["amount"])
        expense = sum(filtered_df[filtered_df["amount"] < 0]["amount"])
        balance = income + expense
        col1, col2, col3 = st.columns(3)
        col1.metric("总收入", f"¥{income:.2f}")
        col2.metric("总支出", f"¥{expense:.2f}")
        col3.metric("当前余额", f"¥{balance:.2f}")
    else:
        st.info("暂无交易记录")

    # 管理员操作
    if is_admin:
        with st.expander("🔧 记录新交易（仅管理员）", expanded=False):
            trans_type = st.radio("交易类型", ["收入", "支出"], horizontal=True)
            col1, col2 = st.columns(2)
            with col1:
                default_amount = 100.0 if trans_type == "收入" else -100.0
                amount = st.number_input("金额 (¥)", value=default_amount, step=10.0)
                if trans_type == "收入" and amount < 0:
                    amount = abs(amount)
                elif trans_type == "支出" and amount > 0:
                    amount = -abs(amount)
            with col2:
                trans_date = st.date_input("交易日期", date.today())
                if trans_date > date.today():
                    st.warning("交易日期不能晚于今天")

            desc = st.text_input("交易描述", "例如：筹款活动、购买办公用品")
            handler = st.text_input("经手人", st.session_state.user)

            if st.button("记录交易"):
                if not desc.strip():
                    st.error("请输入交易描述")
                elif trans_date > date.today():
                    st.error("交易日期不能晚于今天")
                elif amount == 0:
                    st.error("交易金额不能为0")
                else:
                    st.session_state.transactions.append({
                        "id": str(uuid.uuid4()),
                        "date": trans_date.strftime("%Y-%m-%d"),
                        "amount": amount,
                        "desc": desc,
                        "handler": handler
                    })
                    st.success("交易记录成功！")

        # 编辑/删除交易
        if st.session_state.transactions:
            with st.expander("🔧 管理交易记录（仅管理员）", expanded=False):
                trans_options = {
                    f"{t['date']} - {t['desc']} (¥{t['amount']:.2f})": t["id"]
                    for t in st.session_state.transactions
                }
                selected_id = st.selectbox("选择交易", trans_options.values(),
                                         format_func=lambda x: [k for k, v in trans_options.items() if v == x][0])
                selected_trans = next(t for t in st.session_state.transactions if t["id"] == selected_id)

                # 编辑
                st.subheader("编辑交易")
                col1, col2 = st.columns(2)
                with col1:
                    edit_amount = st.number_input("金额 (¥)", value=float(selected_trans["amount"]), step=10.0)
                with col2:
                    edit_date = st.date_input("交易日期", datetime.strptime(selected_trans["date"], "%Y-%m-%d").date())
                edit_desc = st.text_input("描述", selected_trans["desc"])
                edit_handler = st.text_input("经手人", selected_trans["handler"])

                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("保存修改"):
                        if not edit_desc.strip():
                            st.error("请输入描述")
                        elif edit_date > date.today():
                            st.error("日期无效")
                        elif edit_amount == 0:
                            st.error("金额不能为0")
                        else:
                            for t in st.session_state.transactions:
                                if t["id"] == selected_id:
                                    t.update({
                                        "date": edit_date.strftime("%Y-%m-%d"),
                                        "amount": edit_amount,
                                        "desc": edit_desc,
                                        "handler": edit_handler
                                    })
                            st.success("交易已更新")
                with col_del:
                    if st.button("删除交易", type="secondary"):
                        if st.checkbox("确认删除（不可恢复）"):
                            st.session_state.transactions = [t for t in st.session_state.transactions if t["id"] != selected_id]
                            st.success("交易已删除")
