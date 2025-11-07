import streamlit as st
import pandas as pd
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="学生会经费管理系统",
    page_icon="💰",
    layout="wide"  # 宽屏布局更适合紧凑显示
)

# 初始化会话状态（存储数据）
if "members" not in st.session_state:
    st.session_state.members = pd.DataFrame(columns=["姓名", "学生ID", "加入时间"])

if "income" not in st.session_state:
    st.session_state.income = pd.DataFrame(columns=["日期", "收入来源", "金额(元)", "经手人", "备注"])

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["日期", "报销事项", "金额(元)", "经手人", "报销状态", "备注"])

# 定义紧凑分隔线（核心优化：减少模块间间距）
def compact_divider():
    st.markdown("<hr style='margin: 8px 0; height:1px; background-color:#eee;'>", unsafe_allow_html=True)

# ---------------------- 1. 成员管理模块 ----------------------
st.header("👥 成员管理")
st.write("管理成员的基本信息（姓名、学生ID）")
compact_divider()  # 替换默认分隔线，缩减间距

# 添加新成员（紧凑布局：减少子标题间距）
st.markdown("### 添加新成员", unsafe_allow_html=True)  # 比st.subheader更紧凑
col1, col2 = st.columns(2)
with col1:
    new_name = st.text_input("姓名", key="name_input")
with col2:
    new_id = st.text_input("学生ID", key="id_input")

if st.button("添加成员", key="add_member"):
    if new_name and new_id:
        # 检查ID是否重复
        if new_id in st.session_state.members["学生ID"].values:
            st.error("该学生ID已存在！")
        else:
            # 添加新成员
            new_row = pd.DataFrame({
                "姓名": [new_name],
                "学生ID": [new_id],
                "加入时间": [datetime.now().strftime("%Y-%m-%d %H:%M")]
            })
            st.session_state.members = pd.concat([st.session_state.members, new_row], ignore_index=True)
            st.success(f"成功添加成员：{new_name}")
    else:
        st.warning("请填写姓名和学生ID")

# 显示成员列表（减少表格上下间距）
st.markdown("### 成员列表", unsafe_allow_html=True)
if not st.session_state.members.empty:
    st.dataframe(st.session_state.members, use_container_width=True)
    # 删除成员功能
    del_id = st.selectbox("选择要删除的学生ID", st.session_state.members["学生ID"], key="del_member")
    if st.button("删除成员", key="delete_member"):
        st.session_state.members = st.session_state.members[st.session_state.members["学生ID"] != del_id]
        st.success("成员已删除")
else:
    st.info("暂无成员数据，请添加成员")

# ---------------------- 2. 收入管理模块 ----------------------
compact_divider()  # 模块间紧凑分隔
st.header("📈 收入管理")
st.write("记录学生会的各项收入（赞助、会费等）")
compact_divider()

# 添加收入（减少空行）
st.markdown("### 添加收入", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    income_date = st.date_input("日期", datetime.now(), key="income_date")
with col2:
    income_source = st.text_input("收入来源", key="income_source")
with col3:
    income_amount = st.number_input("金额(元)", min_value=0.01, step=0.01, key="income_amount")

col4, col5 = st.columns(2)
with col4:
    income_person = st.text_input("经手人", key="income_person")
with col5:
    income_note = st.text_input("备注", key="income_note")

if st.button("添加收入记录", key="add_income"):
    if income_source and income_amount and income_person:
        new_income = pd.DataFrame({
            "日期": [income_date.strftime("%Y-%m-%d")],
            "收入来源": [income_source],
            "金额(元)": [income_amount],
            "经手人": [income_person],
            "备注": [income_note]
        })
        st.session_state.income = pd.concat([st.session_state.income, new_income], ignore_index=True)
        st.success("收入记录添加成功")
    else:
        st.warning("请填写来源、金额和经手人")

# 显示收入列表
st.markdown("### 收入记录", unsafe_allow_html=True)
if not st.session_state.income.empty:
    st.dataframe(st.session_state.income, use_container_width=True)
    # 计算总收入
    total_income = st.session_state.income["金额(元)"].sum()
    st.markdown(f"**总收入：{total_income:.2f} 元**", unsafe_allow_html=True)
else:
    st.info("暂无收入记录")

# ---------------------- 3. 报销管理模块 ----------------------
compact_divider()  # 模块间紧凑分隔
st.header("🧾 报销管理")
st.write("管理学生会的各项报销申请及审批状态")
compact_divider()

# 添加报销记录
st.markdown("### 添加报销申请", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    exp_date = st.date_input("日期", datetime.now(), key="exp_date")
with col2:
    exp_item = st.text_input("报销事项", key="exp_item")
with col3:
    exp_amount = st.number_input("金额(元)", min_value=0.01, step=0.01, key="exp_amount")

col4, col5, col6 = st.columns(3)
with col4:
    exp_person = st.text_input("经手人", key="exp_person")
with col5:
    exp_status = st.selectbox("报销状态", ["待审批", "已批准", "已驳回"], key="exp_status")
with col6:
    exp_note = st.text_input("备注", key="exp_note")

if st.button("添加报销记录", key="add_expense"):
    if exp_item and exp_amount and exp_person:
        new_expense = pd.DataFrame({
            "日期": [exp_date.strftime("%Y-%m-%d")],
            "报销事项": [exp_item],
            "金额(元)": [exp_amount],
            "经手人": [exp_person],
            "报销状态": [exp_status],
            "备注": [exp_note]
        })
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
        st.success("报销记录添加成功")
    else:
        st.warning("请填写事项、金额和经手人")

# 显示报销列表
st.markdown("### 报销记录", unsafe_allow_html=True)
if not st.session_state.expenses.empty:
    st.dataframe(st.session_state.expenses, use_container_width=True)
    # 计算总报销额
    total_expense = st.session_state.expenses["金额(元)"].sum()
    st.markdown(f"**总报销额：{total_expense:.2f} 元**", unsafe_allow_html=True)
else:
    st.info("暂无报销记录")

# ---------------------- 4. 经费统计（紧凑显示） ----------------------
compact_divider()
st.header("📊 经费统计")
if not st.session_state.income.empty and not st.session_state.expenses.empty:
    balance = st.session_state.income["金额(元)"].sum() - st.session_state.expenses["金额(元)"].sum()
    st.markdown(f"### 当前余额：{balance:.2f} 元", unsafe_allow_html=True)
else:
    st.info("请先添加收入或报销记录以显示统计信息")
