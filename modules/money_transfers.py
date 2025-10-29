import streamlit as st
from datetime import datetime
import uuid

def render_money_transfers():
    # -------------------------- 1. 会话状态初始化（确保首次运行不报错）--------------------------
    if "money_transfers" not in st.session_state:
        st.session_state.money_transfers = []  # 存储所有交易记录
    if "del_seq" not in st.session_state:
        st.session_state.del_seq = -1  # 待删除的序列号（-1=无）
    if "add_tip" not in st.session_state:
        st.session_state.add_tip = {"type": "", "msg": ""}  # 新增提示

    # 页面标题与基础分割线
    st.header("Financial Transactions")
    st.write("=" * 50)

    # -------------------------- 2. 处理删除操作（无刷新，直接移除）--------------------------
    if st.session_state.del_seq != -1:
        del_idx = st.session_state.del_seq - 1  # 序列号→索引（序列号=索引+1）
        if 0 <= del_idx < len(st.session_state.money_transfers):
            st.session_state.money_transfers.pop(del_idx)
            st.success(f"Transaction #{st.session_state.del_seq} deleted successfully!")
        st.session_state.del_seq = -1  # 重置删除标记

    # -------------------------- 3. 交易记录表格（纯列表+st.table，无DataFrame）--------------------------
    st.subheader("Transaction History")
    if not st.session_state.money_transfers:
        st.info("No financial transactions recorded yet (Add a transaction below)")
    else:
        # 步骤1：构造表格数据（纯嵌套列表，无任何pandas依赖）
        # 表头顺序：No.（序列列）→ Date → Amount → Description → Handled By → Transaction Type
        table_header = [
            "No.", 
            "Date", 
            "Amount", 
            "Description", 
            "Handled By", 
            "Transaction Type"
        ]
        table_rows = [table_header]  # 表格第一行为表头
        
        # 遍历交易记录，生成表格行（按表头顺序填充数据）
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq_num = idx + 1  # 序列列
            date_str = trans["Date"].strftime("%Y/%m/%d")  # 日期格式
            # 金额带颜色（用Markdown加粗+颜色标签，避免HTML解析问题）
            if trans["Type"] == "Expense":
                amount_str = f"**<span style='color:red'>¥{trans['Amount']:.2f}</span>**"
            else:
                amount_str = f"**<span style='color:green'>¥{trans['Amount']:.2f}</span>**"
            # 构造表格行（与表头顺序完全一致）
            table_rows.append([
                seq_num,
                date_str,
                amount_str,
                trans["Description"],
                trans["Handler"],
                trans["Type"]
            ])

        # 步骤2：渲染表格（用st.table，纯基础组件，全版本兼容）
        # 关键：用st.markdown逐行渲染，避免st.table对复杂格式的兼容性问题
        st.markdown("| " + " | ".join(table_header) + " |", unsafe_allow_html=True)
        st.markdown("|" + "---|" * len(table_header), unsafe_allow_html=True)  # 表头分隔线
        for row in table_rows[1:]:  # 跳过表头，渲染数据行
            # 逐列处理数据，确保Markdown颜色生效
            formatted_row = []
            for item in row:
                # 若为金额（带HTML标签），直接保留；其他字段转字符串
                if isinstance(item, str) and ("color:red" in item or "color:green" in item):
                    formatted_row.append(item)
                else:
                    formatted_row.append(str(item))
            # 渲染当前行
            st.markdown("| " + " | ".join(formatted_row) + " |", unsafe_allow_html=True)

        # 步骤3：删除按钮区域（按序列号匹配表格）
        st.write("---")
        st.write("Delete Transaction (match 'No.' in the table):")
        for idx, trans in enumerate(st.session_state.money_transfers):
            seq_num = idx + 1
            btn_key = f"del_{trans['uuid']}"  # 唯一按钮key，避免重复
            if st.button(f"Delete Transaction #{seq_num}", key=btn_key):
                st.session_state.del_seq = seq_num
                return render_money_transfers()  # 重调函数执行删除

    # 分割线：区分交易记录与新增区域
    st.write("=" * 50)

    # -------------------------- 4. 新增交易表单（纯基础组件，无复杂配置）--------------------------
    st.subheader("Record New Transaction")
    with st.form("new_trans_form"):
        # 两列布局，优化表单视觉
        col1, col2 = st.columns(2)
        with col1:
            # 对应表格Date列
            trans_date = st.date_input("Transaction Date", value=datetime.today())
            # 对应表格Amount列
            amount = st.number_input("Amount (¥)", min_value=0.01, step=0.01, value=100.00)
            # 对应表格Transaction Type列
            trans_type = st.radio("Transaction Type", ["Income", "Expense"], index=0)
        with col2:
            # 对应表格Description列
            description = st.text_input("Description", value="Fundraiser proceeds").strip()
            # 对应表格Handled By列
            handler = st.text_input("Handled By", value="Pikachu Da Best").strip()

        # 提交按钮
        submit_btn = st.form_submit_button("Record Transaction", use_container_width=True)

        # 表单提交逻辑
        if submit_btn:
            # 校验必填字段
            if not (amount and description and handler):
                st.session_state.add_tip = {"type": "error", "msg": "Required fields: Amount, Description, Handled By!"}
            else:
                # 新增交易到列表（字段与表格一一对应）
                st.session_state.money_transfers.append({
                    "uuid": str(uuid.uuid4()),  # 唯一ID，用于删除按钮key
                    "Date": trans_date,
                    "Amount": round(amount, 2),
                    "Description": description,
                    "Handler": handler,
                    "Type": trans_type
                })
                st.session_state.add_tip = {"type": "success", "msg": "Transaction recorded successfully! (Check the table above)"}
            
            # 重调函数，立即显示新增记录
            return render_money_transfers()

    # 显示新增提示
    if st.session_state.add_tip["type"] == "success":
        st.success(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}
    elif st.session_state.add_tip["type"] == "error":
        st.error(st.session_state.add_tip["msg"])
        st.session_state.add_tip = {"type": "", "msg": ""}
