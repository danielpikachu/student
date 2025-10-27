import streamlit as st

def render_groups(is_admin, user_group):
    """群组模块：管理部门和成员分配"""
    st.subheader("👥 群组管理")
    st.write("管理学生会部门及成员分配")
    st.divider()
    
    # 显示用户所属群组
    st.info(f"你所在的群组：{user_group}")
    
    # 显示所有群组
    st.subheader("所有群组")
    st.dataframe(
        {"群组名称": st.session_state.groups},
        use_container_width=True,
        hide_index=True
    )
    
    # 管理员查看成员分配
    if is_admin:
        st.subheader("成员-群组分配")
        st.dataframe(
            st.session_state.member_groups.items(),
            column_config={"0": "成员", "1": "群组"},
            use_container_width=True,
            hide_index=True
        )
    
    # 管理员操作
    if is_admin:
        with st.expander("🔧 管理群组", expanded=False):
            # 添加群组
            new_group = st.text_input("新群组名称")
            if st.button("添加群组"):
                if new_group and new_group not in st.session_state.groups:
                    st.session_state.groups.append(new_group)
                    st.success(f"已添加群组：{new_group}")
                elif not new_group:
                    st.error("请输入群组名称")
                else:
                    st.error("群组已存在")
            
            # 删除群组
            if st.session_state.groups:
                del_group = st.selectbox("选择删除的群组", st.session_state.groups)
                if st.button("删除群组", type="secondary"):
                    st.session_state.groups.remove(del_group)
                    # 同步删除成员关联
                    st.session_state.member_groups = {
                        k: v for k, v in st.session_state.member_groups.items() if v != del_group
                    }
                    st.success(f"已删除群组：{del_group}")
            
            # 分配成员
            st.subheader("成员分配")
            member = st.text_input("成员姓名")
            target_group = st.selectbox("分配到群组", st.session_state.groups)
            if st.button("保存分配"):
                if member:
                    st.session_state.member_groups[member] = target_group
                    st.success(f"已分配 {member} 到 {target_group}")
                else:
                    st.error("请输入成员姓名")
