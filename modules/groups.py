# modules/groups.py
import streamlit as st
import pandas as pd

def add_member_callback(name, student_id):
    """添加成员的回调函数，独立于主渲染流程"""
    # 验证输入
    if not name.strip():
        st.error("成员姓名不能为空")
        return
    if not student_id.strip():
        st.error("学生ID不能为空")
        return
    if any(m["student_id"] == student_id for m in st.session_state.members):
        st.error(f"学生ID {student_id} 已存在")
        return
    
    # 添加成员
    member_id = f"M{len(st.session_state.members) + 1:03d}"
    st.session_state.members.append({
        "id": member_id,
        "name": name.strip(),
        "student_id": student_id.strip()
    })
    st.success(f"成功添加：{name}（ID：{student_id}）")

def render_groups():
    """三个模块从上到下布局，修复添加按钮点击一次生效"""
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.title("📋 学生事务综合管理系统")
    st.write("包含成员管理、收入管理和报销管理三个功能模块")
    st.divider()

    # 初始化成员数据
    if "members" not in st.session_state:
        st.session_state.members = []  # 结构: [{id, name, student_id}]

    # ---------------------- 1. 成员管理模块 ----------------------
    st.header("👥 成员管理")
    st.write("管理成员的基本信息（姓名、学生ID）")
    st.divider()

    # 成员列表展示（优先展示最新状态）
    st.subheader("成员列表")
    if not st.session_state.members:
        st.info("暂无成员信息，请在下方添加")
    else:
        member_table = [
            {"序号": i+1, "成员姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ]
        st.dataframe(pd.DataFrame(member_table), use_container_width=True)

        # 删除功能
        with st.expander("管理成员（删除）"):
            for m in st.session_state.members:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_mem_{m['id']}", use_container_width=True):
                        st.session_state.members = [mem for mem in st.session_state.members if mem["id"] != m["id"]]
                        st.success(f"已删除成员：{m['name']}")
                        st.rerun()

    st.divider()

    # 添加新成员（使用回调函数确保状态立即更新）
    st.subheader("添加新成员")
    
    # 使用普通输入框而非表单，避免表单提交的状态延迟
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("成员姓名*", placeholder="请输入姓名", key="name_input")
    with col2:
        student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID", key="id_input")
    
    # 添加按钮绑定回调函数
    if st.button("确认添加", use_container_width=True):
        add_member_callback(name, student_id)
        # 强制刷新页面（仅在添加成功后）
        if name.strip() and student_id.strip() and not any(m["student_id"] == student_id for m in st.session_state.members):
            st.rerun()

    # 模块间分隔
    st.write("---")
    st.write("# ")

    # ---------------------- 2. 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    st.divider()
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
