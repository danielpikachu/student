import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    # 核心状态：存储交易、删除标记、新增提示
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 交易列表（存储所有新增记录）
    if "del_seq" not in st.session_state:
        st.session_state.del_seq = -1  # 待删除的「序列号」（-1=无）
    if "add_tip" not in st.session_state:
        st.session_state.add_tip = {"type": "", "msg": ""}  # 新增提示（success/error + 消息）

    # 页面标题与分割线（基础组件，全版本兼容）
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 先处理删除操作（根据序列号定位，无刷新）--------------------------
    # 若有标记待删除的序列号，直接从列表中移除
    if st.session_state.del_seq != -1:
        # 序列号=索引+1，通过序列号找索引
        del_idx = st.session_state.del_seq - 1
        if 0 <= del_idx < len(st.session_state.money_transfers):
            st.session_state.money_transfers.pop(del_idx)
            st.success(f"Transaction #{st.session_state.del_seq} deleted successfully!")
        st.session_state.del_seq = -1  # 重置删除标记

    # -------------------------- 3. 交易记录表格（按指定表头显示，含序列列）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 步骤1：构造表格数据（严格按「序列列+指定表头」顺序）
        table_data = []
        for idx, trans in enumerate(st.session_state.money_transfers):
            # 处理金额显示：支出红、收入绿（HTML标签）
            amount_color = "red" if trans["Type"] == "Expense" else "green"
            amount_text = f"¥{trans['Amount']:.2f}"  # 金额无负号，通过Type列区分收支
            amount_html = f"<span style='color:{amount_color}'>{amount_text}</span>"
            
            # 表格行数据：顺序=序列列 → 指定表头（date, amount, description, handled by, transaction type）
            table_data.append([
                idx + 1,  # 序列列（第一列）
                trans["Date"].strftime("%Y/%m/%d"),  # Date（指定表头1）
                amount_html,  # Amount（指定表头2，带颜色）
                trans["Description"],  # Description（指定表头3）
                trans["Handler"],  # Handled By（指定表头4，修正拼写：原handledy by→Handled By）
                trans["Type"]  # Transaction Type（指定表头5）
            ])

        # 步骤2：渲染表格（严格按指定表头命名，无复杂参数）
        st.dataframe(
            pd.DataFrame(
                table_data,
                columns=[
                    "No.",  # 序列列标题
                    "Date",  # 指定表头1
                    "Amount",  # 指定表头2
                    "Description",  # 指定表头3
                    "Handled By",  # 指定表头4（修正拼写错误）
                    "Transaction Type"  # 指定表头5
                ]
            ),
            index=False,  # 隐藏默认索引，仅显示自定义序列列
            escape=False  # 允许解析HTML，显示金额颜色
        )

        # 步骤3：删除按钮区域（按序列号匹配表格，点击标记删除）
        st.write("---")
        st.write("Delete Transaction (match 'No.' in the table):")
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq_num = idx + 1  # 与表格序列列一致
            btn_key = f"del_{trans['uuid']}"  # 唯一按钮key，避免重复
            # 点击按钮→标记待删除序列号→重新执行函数（无刷新）
            if st.button(f"Delete Transaction #{seq_num}", key=btn_key):
                st.session_state.del_seq = seq_num
                return render_money_transfers()  # 重调函数执行删除

    # 分割线：区分交易记录与新增区域
    st.write("=" * 50)

    # -------------------------- 4. 新增交易表单（提交后直接更新表格）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form"):  # 纯基础表单，无兼容性问题
        # 表单字段：与表格表头一一对应（顺序无关，提交时匹配字段）
        col1, col2 = st.columns(2)  # 两列布局，优化视觉
        with col1:
            # Date（对应表格Date列）
            trans_date = st.date_input("Transaction Date", value=datetime.today())
            # Amount（对应表格Amount列）
            amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
            # Transaction Type（对应表格Transaction Type列）
            trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
        with col2:
            # Description（对应表格Description列）
            description = st.text_input("Description", value="Fundraiser proceeds").strip()
            # Handled By（对应表格Handled By列，修正拼写）
            handler = st.text_input("Handled By", value="Pikachu Da Best").strip()

        # 提交按钮
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)

        # 表单提交逻辑：新增记录→更新表格
        if submit_btn:
            # 校验必填字段（确保表格数据完整）
            if not (amount and description and handler):
                st.session_state.add_tip = {"type": "error", "msg": "Required fields: Amount, Description, Handled By!"}
            else:
                # 新增交易到列表（字段与表格一一对应）
                st.session_state.money_transfers.append({
                    "uuid": str(uuid.uuid4()),  # 唯一ID，用于删除按钮key
                    "Date": trans_date,  # 对应表格Date列
                    "Amount": round(amount, 2),  # 对应表格Amount列
                    "Description": description,  # 对应表格Description列
                    "Handler": handler,  # 对应表格Handled By列
                    "Type": trans_type  # 对应表格Transaction Type列
                })
                st.session_state.add_tip = {"type": "success", "msg": "Transaction recorded successfully! (Check the table above)"}
            
            # 重调函数，立即显示新增记录（无刷新）
            return render_money_transfers()

    # 显示新增提示（成功/错误）
    if st.session_state.add_tip["type"] == "success":
        st.success(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}  # 重置提示
    elif st.session_state.add_tip["type"] == "error":
        st.error(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}  # 重置提示
