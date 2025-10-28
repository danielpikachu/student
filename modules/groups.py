import streamlit as st

def render_groups():
    st.header("Groups Management")
    st.write("Manage student council groups, departments, and their members here.")
    st.divider()
    
    # 子选项卡：社团列表/成员列表/添加数据
    groups_tab, members_tab, add_tab = st.tabs(["Groups List", "Members List", "Add New Data"])
    
    with groups_tab:
        st.subheader("Existing Groups")
        if st.session_state.groups:
            for i, group in enumerate(st.session_state.groups):
                with st.card():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(group["GroupName"])
                        st.write(f"👤 Leader: {group['Leader']}")
                        st.write(f"👥 Member Count: {group['MemberCount']}")
                        if group["Description"]:
                            st.caption(f"Description: {group['Description']}")
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("Delete", key=f"group_del_{i}"):
                            group_id = group["GroupID"]
                            # 删除社团
                            st.session_state.groups.pop(i)
                            # 删除关联成员
                            st.session_state.group_members = [
                                m for m in st.session_state.group_members 
                                if m["GroupID"] != group_id
                            ]
                            st.success("Group deleted successfully!")
                            st.experimental_rerun()
        else:
            st.info("No groups created yet. Add a group using the 'Add New Data' tab.")
    
    with members_tab:
        st.subheader("Group Members")
        if st.session_state.groups:
            # 选择社团
            group_names = [g["GroupName"] for g in st.session_state.groups]
            selected_group = st.selectbox("Select a Group", group_names)
            
            # 获取选中社团的ID
            group_id = next(g["GroupID"] for g in st.session_state.groups 
                          if g["GroupName"] == selected_group)
            
            # 筛选该社团的成员
            group_members = [m for m in st.session_state.group_members 
                           if m["GroupID"] == group_id]
            
            if group_members:
                for i, member in enumerate(group_members):
                    with st.card():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader(member["Name"])
                            st.write(f"🆔 Student ID: {member['StudentID']}")
                            st.write(f"🔖 Position: {member['Position']}")
                            if member["Contact"]:
                                st.write(f"📞 Contact: {member['Contact']}")
                    with col2:
                        st.write("")
                        st.write("")
                        if st.button("Delete", key=f"mem_del_{i}"):
                            st.session_state.group_members.pop(i)
                            # 更新成员计数
                            for g in st.session_state.groups:
                                if g["GroupID"] == group_id:
                                    g["MemberCount"] -= 1
                            st.success("Member deleted successfully!")
                            st.experimental_rerun()
            else:
                st.info(f"No members in {selected_group} yet. Add members using the 'Add New Data' tab.")
        else:
            st.info("No groups available. Create a group first.")
    
    with add_tab:
        # 选择添加社团或成员
        option = st.radio("Select Action", ["Add New Group", "Add New Member"])
        
        if option == "Add New Group":
            st.subheader("Create Group")
            with st.form("new_group_form", clear_on_submit=True):
                group_name = st.text_input("Group Name *")
                leader = st.text_input("Group Leader *")
                description = st.text_area("Group Description (Optional)")
                
                submit = st.form_submit_button("Create Group", use_container_width=True)
                
                if submit:
                    if not all([group_name, leader]):
                        st.error("Fields marked with * are required!")
                    else:
                        # 生成唯一ID
                        group_id = f"G{len(st.session_state.groups) + 1:03d}"
                        st.session_state.groups.append({
                            "GroupID": group_id,
                            "GroupName": group_name,
                            "Leader": leader,
                            "Description": description,
                            "MemberCount": 0
                        })
                        st.success(f"Group '{group_name}' created successfully!")
        
        else:  # 添加成员
            if st.session_state.groups:
                st.subheader("Add Member to Group")
                with st.form("new_member_form", clear_on_submit=True):
                    # 选择所属社团
                    group_names = [g["GroupName"] for g in st.session_state.groups]
                    selected_group = st.selectbox("Select Group *", group_names)
                    
                    # 成员信息
                    name = st.text_input("Member Name *")
                    student_id = st.text_input("Student ID *")
                    position = st.text_input("Position *")
                    contact = st.text_input("Contact Information (Optional)")
                    
                    submit = st.form_submit_button("Add Member", use_container_width=True)
                    
                    if submit:
                        if not all([selected_group, name, student_id, position]):
                            st.error("Fields marked with * are required!")
                        else:
                            # 获取社团ID
                            group_id = next(g["GroupID"] for g in st.session_state.groups 
                                          if g["GroupName"] == selected_group)
                            # 生成成员ID
                            member_id = f"M{len(st.session_state.group_members) + 1:03d}"
                            # 添加成员
                            st.session_state.group_members.append({
                                "MemberID": member_id,
                                "GroupID": group_id,
                                "Name": name,
                                "StudentID": student_id,
                                "Position": position,
                                "Contact": contact
                            })
                            # 更新社团成员数
                            for g in st.session_state.groups:
                                if g["GroupID"] == group_id:
                                    g["MemberCount"] += 1
                            st.success(f"Member '{name}' added to {selected_group} successfully!")
            else:
                st.info("No groups available. Create a group first to add members.")
