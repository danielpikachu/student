import streamlit as st

def render_groups(is_admin, user_group):
    st.subheader("👥 Groups")
    st.write("Manage student council groups and member assignments")
    st.divider()
    
    # 显示用户所属群组
    st.info(f"Your Group: {user_group}")
    
    # 显示所有群组
    st.subheader("All Groups")
    st.dataframe(
        {"Group Name": st.session_state.groups},
        use_container_width=True,
        hide_index=True
    )
    
    # 管理员查看成员分配
    if is_admin:
        st.subheader("Member-Group Assignments")
        st.dataframe(
            st.session_state.member_groups.items(),
            column_config={"0": "Member", "1": "Group"},
            use_container_width=True,
            hide_index=True
        )
    
    # 管理员操作
    if is_admin:
        with st.expander("🔧 Manage Groups (Admin Only)", expanded=False):
            # 添加群组
            new_group = st.text_input("New Group Name")
            if st.button("Add Group"):
                if new_group and new_group not in st.session_state.groups:
                    st.session_state.groups.append(new_group)
                    st.success(f"Group '{new_group}' added successfully")
                elif not new_group:
                    st.error("Please enter a group name")
                else:
                    st.error("Group already exists")
            
            # 删除群组
            if st.session_state.groups:
                del_group = st.selectbox("Select Group to Delete", st.session_state.groups)
                if st.button("Delete Group", type="secondary"):
                    st.session_state.groups.remove(del_group)
                    # 同步删除成员关联
                    st.session_state.member_groups = {
                        k: v for k, v in st.session_state.member_groups.items() if v != del_group
                    }
                    st.success(f"Group '{del_group}' deleted successfully")
            
            # 分配成员
            st.subheader("Assign Member to Group")
            member = st.text_input("Member Name")
            target_group = st.selectbox("Assign to Group", st.session_state.groups)
            if st.button("Save Assignment"):
                if member:
                    st.session_state.member_groups[member] = target_group
                    st.success(f"Member '{member}' assigned to '{target_group}'")
                else:
                    st.error("Please enter a member name")
