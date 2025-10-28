import streamlit as st

def render_groups():
    # 功能选项卡
    tab1, tab2, tab3 = st.tabs(["View Groups", "View Members", "Add Data"])
    
    with tab1:
        st.subheader("Groups List")
        if st.session_state.groups:
            for i, group in enumerate(st.session_state.groups):
                cols = st.columns([2, 1, 1, 1])
                cols[0].write(group["GroupName"])
                cols[1].write(group["Leader"])
                cols[2].write(f"Members: {group['MemberCount']}")
                if cols[3].button("Delete", key=f"group_del_{i}"):
                    # 删除社团及关联成员（使用 GroupID 关联）
                    group_id = group["GroupID"]
                    st.session_state.groups.pop(i)
                    st.session_state.group_members = [
                        m for m in st.session_state.group_members 
                        if m["GroupID"] != group_id
                    ]
                    st.success("Group deleted")
                    st.experimental_rerun()
        else:
            st.info("No groups yet. Add a new group.")
    
    with tab2:
        st.subheader("Group Members")
        if st.session_state.groups:
            # 选择社团（显示 GroupName）
            group_names = [g["GroupName"] for g in st.session_state.groups]
            selected_group = st.selectbox("Select Group", group_names)
            
            # 通过 GroupID 关联成员（标准化关联字段）
            group_id = next(g["GroupID"] for g in st.session_state.groups 
                          if g["GroupName"] == selected_group)
            members = [m for m in st.session_state.group_members 
                      if m["GroupID"] == group_id]
            
            if members:
                for i, member in enumerate(members):
                    cols = st.columns([2, 1, 1, 2, 1])
                    cols[0].write(member["Name"])
                    cols[1].write(member["StudentID"])
                    cols[2].write(member["Position"])
                    cols[3].write(member["Contact"])
                    if cols[4].button("Delete", key=f"mem_del_{i}"):
                        st.session_state.group_members.pop(i)
                        # 更新成员计数（通过 GroupID 定位）
                        for g in st.session_state.groups:
                            if g["GroupID"] == group_id:
                                g["MemberCount"] -= 1
                        st.success("Member deleted")
                        st.experimental_rerun()
            else:
                st.info(f"No members in {selected_group}. Add members.")
        else:
            st.info("Create a group first to add members.")
    
    with tab3:
        option = st.radio("Select Action", ["Add Group", "Add Member"])
        
        if option == "Add Group":
            with st.form("new_group"):
                group_name = st.text_input("Group Name*")
                leader = st.text_input("Leader*")
                description = st.text_area("Description")
                
                submit = st.form_submit_button("Create Group")
                
                if submit:
                    if not all([group_name, leader]):
                        st.error("Fields marked with * are required")
                    else:
                        # 生成唯一 GroupID（为同步到 Google Sheet 做准备）
                        group_id = f"G{len(st.session_state.groups) + 1:03d}"
                        st.session_state.groups.append({
                            "GroupID": group_id,
                            "GroupName": group_name,
                            "Leader": leader,
                            "Description": description,
                            "MemberCount": 0
                        })
                        st.success(f"Group {group_name} created!")
        
        else:  # Add Member
            if st.session_state.groups:
                with st.form("new_member"):
                    group_names = [g["GroupName"] for g in st.session_state.groups]
                    selected_group = st.selectbox("Belong to Group*", group_names)
                    name = st.text_input("Member Name*")
                    student_id = st.text_input("Student ID*")
                    position = st.text_input("Position*")
                    contact = st.text_input("Contact")
                    
                    submit = st.form_submit_button("Add Member")
                    
                    if submit:
                        if not all([selected_group, name, student_id, position]):
                            st.error("Fields marked with * are required")
                        else:
                            # 获取关联的 GroupID
                            group_id = next(g["GroupID"] for g in st.session_state.groups 
                                          if g["GroupName"] == selected_group)
                            # 生成唯一 MemberID
                            member_id = f"M{len(st.session_state.group_members) + 1:03d}"
                            st.session_state.group_members.append({
                                "MemberID": member_id,
                                "GroupID": group_id,
                                "Name": name,
                                "StudentID": student_id,
                                "Position": position,
                                "Contact": contact
                            })
                            # 更新社团成员计数
                            for g in st.session_state.groups:
                                if g["GroupID"] == group_id:
                                    g["MemberCount"] += 1
                            st.success(f"Member {name} added!")
            else:
                st.info("Create a group first to add members.")
