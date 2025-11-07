# modules/groups.py
import streamlit as st
import pandas as pd

def render_groups():
    """进一步压缩布局，减少所有不必要的空白区域"""
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.title("📋 学生事务综合管理系统")
    st.caption("成员、收入和报销管理功能")  # 缩短说明文字并使用caption减小占用空间
    st.divider()

    # 初始化成员数据
    if "members" not in st.session_state:
        st.session_state.members = []

    # ---------------------- 1. 成员管理模块 ----------------------
    st.header("👥 成员管理")
    st.write("管理成员基本信息（姓名、学生ID）", help="添加/删除成员信息")
    st.divider()

    # 添加新成员区域（紧凑排列）
    st.subheader("添加新成员", divider="gray")  # 使用小型分隔线替代st.divider()
    col1, col2, col3 = st.columns([3, 3, 1.5])  # 调整列宽比例，让按钮更紧凑
    with col1:
        name = st.text_input("成员姓名*", placeholder="姓名", label_visibility="collapsed")
    with col2:
        student_id = st.text_input("学生ID*", placeholder="唯一ID", label_visibility="collapsed")
    with col3:
        add_btn = st.button("确认添加", use_container_width=True, key="add_btn")

    # 添加按钮逻辑（紧跟输入框，无额外间距）
    if add_btn:
        valid = True
        if not name.strip():
            st.error("姓名不能为空", icon="❌")
            valid = False
        if not student_id.strip():
            st.error("学生ID不能为空", icon="❌")
            valid = False
        if any(m["student_id"] == student_id for m in st.session_state.members):
            st.error(f"ID {student_id} 已存在", icon="❌")
            valid = False

        if valid:
            member_id = f"M{len(st.session_state.members) + 1:03d}"
            st.session_state.members.append({
                "id": member_id,
                "name": name.strip(),
                "student_id": student_id.strip()
            })
            st.success(f"添加成功：{name}", icon="✅")

    # 成员列表展示（压缩高度和间距）
    st.subheader("成员列表", divider="gray")
    if not st.session_state.members:
        st.info("暂无成员，请添加", icon="ℹ️")
    else:
        # 动态调整表格高度，最小化空白
        member_df = pd.DataFrame([
            {"序号": i+1, "成员姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ])
        st.dataframe(
            member_df, 
            use_container_width=True,
            height=min(200, 40 + len(st.session_state.members)*30)  # 更紧凑的高度计算
        )

        # 删除功能（无额外空行）
        with st.expander("管理成员", expanded=False):  # 缩短标题
            for m in st.session_state.members:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{m['name']}（{m['student_id']}）", unsafe_allow_html=True)  # 缩短显示文本
                with col2:
                    if st.button("删除", key=f"del_mem_{m['id']}", use_container_width=True):
                        st.session_state.members = [mem for mem in st.session_state.members if mem["id"] != m["id"]]
                        st.success(f"已删除：{m['name']}")
                        st.rerun()

    # 模块间分隔（无空行）
    st.divider()

    # ---------------------- 2. 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("记录和管理各项收入信息")
    st.divider()
    st.info("收入管理功能开发中", icon="🔄")

    # 模块间分隔（无空行）
    st.divider()

    # ---------------------- 3. 报销管理模块 ----------------------
    st.header("🧾 报销管理")
    st.write("管理报销申请及审批流程")
    st.divider()
    st.info("报销管理功能开发中", icon="🔄")
