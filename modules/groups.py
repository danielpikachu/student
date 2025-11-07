import streamlit as st
import pandas as pd

def render_groups():
    """成员管理、收入和报销三个模块的完整界面"""
    st.header("📋 学生事务管理系统")
    st.write("统一管理成员信息、收入账记录和报销申请")
    st.divider()

    # 创建三个模块的标签页
    tab1, tab2, tab3 = st.tabs(["👥 成员管理", "💰 收入管理", "🧾 报销管理"])

    # ---------------------- 第一块：成员管理（已实现） ----------------------
    with tab1:
        # 初始化成员会话状态
        if "members" not in st.session_state:
            st.session_state.members = []  # 结构: [{id, name, student_id}]

        # 成员列表展示
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
                            st.rerun()

        st.markdown("---")

        # 添加新成员
        st.subheader("添加新成员")
        with st.form("member_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                member_name = st.text_input("成员姓名", placeholder="请输入姓名", key="name_input")
            with col2:
                student_id = st.text_input("学生ID", placeholder="请输入学生ID", key="id_input")

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

    # ---------------------- 第二块：收入管理（预留模块） ----------------------
    with tab2:
        st.subheader("收入记录管理")
        st.write("用于记录各项收入明细，包括来源、金额、日期等信息")
        
        # 初始化收入会话状态
        if "income_records" not in st.session_state:
            st.session_state.income_records = []  # 预留数据结构

        # 示例：简单的功能占位
        if not st.session_state.income_records:
            st.info("暂无收入记录，后续可在此添加收入信息")
        else:
            # 未来可实现收入表格展示
            pass

        st.markdown("---")
        
        # 预留添加收入的表单位置
        with st.expander("添加新收入（待实现）", expanded=False):
            st.write("此处将实现收入信息录入功能")
            # 未来可添加：
            # 收入来源、金额、日期、经手人等字段

    # ---------------------- 第三块：报销管理（预留模块） ----------------------
    with tab3:
        st.subheader("报销申请管理")
        st.write("用于管理报销申请，包括申请人、金额、事由、状态等信息")
        
        # 初始化报销会话状态
        if "reimbursement_records" not in st.session_state:
            st.session_state.reimbursement_records = []  # 预留数据结构

        # 示例：简单的功能占位
        if not st.session_state.reimbursement_records:
            st.info("暂无报销记录，后续可在此添加报销信息")
        else:
            # 未来可实现报销表格展示
            pass

        st.markdown("---")
        
        # 预留添加报销的表单位置
        with st.expander("添加新报销（待实现）", expanded=False):
            st.write("此处将实现报销信息录入功能")
            # 未来可添加：
            # 申请人、金额、事由、日期、凭证上传等字段

# 执行主函数
if __name__ == "__main__":
    render_groups()
