# modules/groups.py
import streamlit as st
import pandas as pd

def render_groups():
    """优化布局紧凑性，减少不必要空白"""
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.markdown(
    "<p style='line-height: 0.5; font-size: 24px;'>📋 学生事务综合管理系统</p>",
    unsafe_allow_html=True
    )
    st.caption("包含成员管理、收入管理和报销管理三个功能模块")  # 使用caption减小字体和间距
    st.divider()

    # 初始化成员数据
    if "members" not in st.session_state:
        st.session_state.members = []

    # ---------------------- 1. 成员管理模块 ----------------------
    st.markdown(
    "<p style='line-height: 0.5; font-size: 20px;'>👥 成员管理</p>",
    unsafe_allow_html=True
    )
    st.write("管理成员的基本信息（姓名、学生ID）")
    st.divider()

    # 添加新成员区域（紧凑布局）
    with st.container():  # 使用容器减少外部间距
        st.subheader("添加新成员")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("成员姓名*", placeholder="请输入姓名", label_visibility="visible")
        with col2:
            student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID", label_visibility="visible")
        
        # 确认添加按钮紧跟输入框
        if st.button("确认添加", use_container_width=True, key="add_btn"):
            valid = True
            if not name.strip():
                st.error("成员姓名不能为空", icon="❌")
                valid = False
            if not student_id.strip():
                st.error("学生ID不能为空", icon="❌")
                valid = False
            if any(m["student_id"] == student_id for m in st.session_state.members):
                st.error(f"学生ID {student_id} 已存在", icon="❌")
                valid = False

            if valid:
                member_id = f"M{len(st.session_state.members) + 1:03d}"
                st.session_state.members.append({
                    "id": member_id,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                })
                st.success(f"成功添加：{name}（ID：{student_id}）", icon="✅")

    st.divider()

    # 成员列表展示
    st.subheader("成员列表")
    if not st.session_state.members:
        st.info("暂无成员信息，请在上方添加", icon="ℹ️")
    else:
        member_df = pd.DataFrame([
            {"序号": i+1, "成员姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ])
        st.dataframe(member_df, use_container_width=True, height=min(300, 50 + len(st.session_state.members)*35))  # 动态调整高度

        # 删除功能（紧凑布局）
        with st.expander("管理成员（删除）", expanded=False):
            for m in st.session_state.members:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    st.button("删除", key=f"del_mem_{m['id']}", use_container_width=True)

    # 模块间分隔（减少空白）
    st.markdown("---")

    # ---------------------- 2. 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    st.divider()
    st.info("收入管理模块区域 - 后续功能将在此处开发", icon="ℹ️")

    # 模块间分隔
    st.markdown("---")

    # ---------------------- 3. 报销管理模块 ----------------------
    st.header("🧾 报销管理")
    st.write("此模块用于管理各项报销申请及审批流程")
    st.divider()
    st.info("报销管理模块区域 - 后续功能将在此处开发", icon="ℹ️")
