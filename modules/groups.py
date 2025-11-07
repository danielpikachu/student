import streamlit as st
import pandas as pd

def render_groups():
    """仅保留成员姓名和学生ID的手动输入与管理功能"""
    st.header("👥 成员管理")
    st.write("添加和管理成员信息（仅需姓名和学生ID）")
    st.divider()

    # 初始化会话状态（仅保留必要字段）
    if "members" not in st.session_state:
        st.session_state.members = []  # 存储成员列表：[{name, student_id, id}]

    # ---------------------- 成员信息输入区域 ----------------------
    st.subheader("添加新成员")
    
    with st.form("member_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            member_name = st.text_input("成员姓名", placeholder="请输入姓名", key="name_input")
        
        with col2:
            student_id = st.text_input("学生ID", placeholder="请输入学生ID", key="id_input")

        # 提交按钮
        submit = st.form_submit_button("添加成员", use_container_width=True)

        if submit:
            # 验证必填字段
            if not member_name.strip():
                st.error("请输入成员姓名")
                return
            if not student_id.strip():
                st.error("请输入学生ID")
                return

            # 检查学生ID是否重复
            if any(m["student_id"] == student_id for m in st.session_state.members):
                st.error(f"学生ID {student_id} 已存在")
                return

            # 生成唯一ID
            member_unique_id = f"M{len(st.session_state.members) + 1:03d}"
            
            # 添加到成员列表
            st.session_state.members.append({
                "id": member_unique_id,
                "name": member_name.strip(),
                "student_id": student_id.strip()
            })

            st.success(f"已添加成员：{member_name}（{student_id}）")

    st.markdown("---")

    # ---------------------- 成员列表与删除功能 ----------------------
    st.subheader("成员列表")
    if not st.session_state.members:
        st.info("暂无成员信息，请添加成员")
    else:
        # 展示成员表格
        member_table = [
            {
                "序号": i + 1,
                "成员姓名": m["name"],
                "学生ID": m["student_id"]
            }
            for i, m in enumerate(st.session_state.members)
        ]
        st.dataframe(pd.DataFrame(member_table), use_container_width=True)

        # 删除功能
        with st.expander("管理成员（删除）"):
            for m in st.session_state.members:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{m['name']}（{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_{m['id']}", use_container_width=True):
                        st.session_state.members = [
                            member for member in st.session_state.members
                            if member["id"] != m["id"]
                        ]
                        st.success(f"已删除成员：{m['name']}")
                        st.rerun()  # 使用最新的rerun方法
