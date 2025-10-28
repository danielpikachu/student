import streamlit as st

def render_groups(is_admin, user_groups):
    # 确保用户群组为列表格式
    if not isinstance(user_groups, list):
        user_groups = [user_groups] if user_groups else ["未分配"]

    st.subheader("👥 群组管理")
    st.write("管理学生会群组及成员分配")
    st.divider()

    # 显示用户所属群组
    if user_groups and user_groups != ["未分配"]:
        st.info(f"你所属的群组: {', '.join(user_groups)}")
    else:
        st.warning("你尚未分配到任何群组")

    # 显示所有群组
    st.subheader("所有群组")
    if st.session_state.groups:
        st.dataframe(
            {"群组名称": st.session_state.groups},
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无创建的群组，请管理员添加群组")

    # 管理员查看成员分配
    if is_admin:
        st.subheader("成员-群组分配")
        if st.session_state.member_groups:
            member_data = [{"成员": m, "所属群组": g} for m, g in st.session_state.member_groups.items()]
            st.dataframe(member_data, use_container_width=True, hide_index=True)
        else:
            st.info("暂无成员分配记录")

    # 管理员操作
    if is_admin:
        with st.expander("🔧 管理群组（仅管理员）", expanded=False):
            # 添加群组
            new_group = st.text_input("新群组名称")
            if st.button("添加群组"):
                if new_group and new_group not in st.session_state.groups:
                    st.session_state.groups.append(new_group)
                    st.success(f"群组 '{new_group}' 添加成功")
                elif not new_group:
                    st.error("请输入群组名称")
                else:
                    st.error("该群组已存在")

            # 删除群组
            if st.session_state.groups:
                del_group = st.selectbox("选择要删除的群组", st.session_state.groups)
                if st.button("删除群组", type="secondary"):
                    st.session_state.groups.remove(del_group)
                    # 同步删除成员关联
                    st.session_state.member_groups = {
                        k: v for k, v in st.session_state.member_groups.items() if v != del_group
                    }
                    st.success(f"群组 '{del_group}' 已删除")

            # 分配成员
            if st.session_state.groups:
                st.subheader("分配成员到群组")
                member = st.text_input("成员姓名")
                target_group = st.selectbox("目标群组", st.session_state.groups)
                if st.button("保存分配"):
                    if member:
                        st.session_state.member_groups[member] = target_group
                        st.success(f"成员 '{member}' 已分配到 '{target_group}'")
                    else:
                        st.error("请输入成员姓名")
