# modules/groups.py
import streamlit as st
import pandas as pd

def render_groups():
    """修复输入框状态修改导致的错误，确保添加按钮一次生效"""
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.title("📋 学生事务综合管理系统")
    st.write("包含成员管理、收入管理和报销管理三个功能模块")
    st.divider()

    # 初始化成员数据
    if "members" not in st.session_state:
        st.session_state.members = []

    # ---------------------- 1. 成员管理模块 ----------------------
    st.header("👥 成员管理")
    st.write("管理成员的基本信息（姓名、学生ID）")
    compact_divider()

    # 添加新成员区域（放在列表上方）
    st.subheader("添加新成员")
    col1, col2 = st.columns(2)
    with col1:
        # 不指定key，避免手动修改session_state冲突
        name = st.text_input("成员姓名*", placeholder="请输入姓名")
    with col2:
        student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID")

    # 添加按钮逻辑
    if st.button("确认添加", use_container_width=True, key="add_btn"):
        valid = True
        if not name.strip():
            st.error("成员姓名不能为空")
            valid = False
        if not student_id.strip():
            st.error("学生ID不能为空")
            valid = False
        if any(m["student_id"] == student_id for m in st.session_state.members):
            st.error(f"学生ID {student_id} 已存在")
            valid = False

        if valid:
            member_id = f"M{len(st.session_state.members) + 1:03d}"
            st.session_state.members.append({
                "id": member_id,
                "name": name.strip(),
                "student_id": student_id.strip()
            })
            st.success(f"成功添加：{name}（ID：{student_id}）")
            # 移除对输入框session_state的直接修改，改用表单的clear_on_submit

    st.divider()

    # 成员列表展示
    st.subheader("成员列表")
    if not st.session_state.members:
        st.info("暂无成员信息，请在上方添加")
    else:
        member_df = pd.DataFrame([
            {"序号": i+1, "成员姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ])
        st.dataframe(member_df, use_container_width=True)

        # 删除功能
        with st.expander("管理成员（删除）"):
            for m in st.session_state.members:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_mem_{m['id']}", use_container_width=True):
                        st.session_state.members = [
                            mem for mem in st.session_state.members 
                            if mem["id"] != m["id"]
                        ]
                        st.success(f"已删除成员：{m['name']}")
                        st.rerun()

    # 模块间分隔
    st.write("---")
    st.write("# ")

    # ---------------------- 2. 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    compact_divider()
    st.info("收入管理模块区域 - 后续功能将在此处开发")
    st.write("")
    st.write("")

    # 模块间分隔
    st.write("---")
    st.write("# ")

    # ---------------------- 3. 报销管理模块 ----------------------
    st.header("🧾 报销管理")
    st.write("此模块用于管理各项报销申请及审批流程")
    st.divider()
    st.info("报销管理模块区域 - 后续功能将在此处开发")
    st.write("")
    st.write("")
