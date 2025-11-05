# modules/groups.py
import streamlit as st
import pandas as pd

def render_groups():
    """渲染群组模块界面（grp_前缀命名空间）"""
    st.header("👥 Groups Management")
    st.write("Import and manage group and member data")
    st.divider()

    # ---------------------- 数据导入区域 ----------------------
    st.subheader("Import Data from File")
    st.write("Supported formats: .xlsx, .csv")
    
    # 选择导入类型
    import_type = st.radio(
        "Select data type to import",
        ["Groups", "Members"],
        key="grp_radio_import_type"  # 层级化Key：grp_模块_单选框_导入类型
    )
    
    # 文件上传组件
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"],
        key="grp_upload_file"  # 层级化Key：grp_模块_上传组件_文件
    )
    
    # 导入按钮
    if st.button("Import Data", key="grp_btn_import", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a file first!")
            return
        
        try:
            # 读取文件
            if uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
            else:  # CSV格式
                df = pd.read_csv(uploaded_file)
            
            # 处理导入逻辑
            if import_type == "Groups":
                # 验证必要列
                required_cols = ["GroupName", "Leader"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Groups file must contain columns: {', '.join(required_cols)}")
                    return
                
                # 处理每一行数据
                added_count = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    leader = str(row["Leader"]).strip()
                    description = str(row.get("Description", "")).strip()
                    
                    # 验证数据有效性
                    if not group_name or not leader:
                        st.warning(f"Skipping invalid row: GroupName or Leader missing")
                        continue
                    
                    # 检查重复
                    if any(g["GroupName"] == group_name for g in st.session_state.grp_list):
                        st.warning(f"Skipping duplicate group: {group_name}")
                        continue
                    
                    # 生成群组ID（G+3位数字，如G001）
                    group_id = f"G{len(st.session_state.grp_list) + 1:03d}"
                    
                    # 添加到会话状态
                    st.session_state.grp_list.append({
                        "GroupID": group_id,
                        "GroupName": group_name,
                        "Leader": leader,
                        "Description": description,
                        "MemberCount": 0  # 初始成员数为0
                    })
                    added_count += 1
                
                st.success(f"Successfully imported {added_count} new groups!")
            
            else:  # 导入成员
                # 验证必要列
                required_cols = ["GroupName", "Name", "StudentID", "Position"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Members file must contain columns: {', '.join(required_cols)}")
                    return
                
                # 检查是否存在群组
                if not st.session_state.grp_list:
                    st.error("No existing groups. Please create groups first.")
                    return
                
                # 处理每一行数据
                added_count = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    member_name = str(row["Name"]).strip()
                    student_id = str(row["StudentID"]).strip()
                    position = str(row["Position"]).strip()
                    contact = str(row.get("Contact", "")).strip()
                    
                    # 验证数据有效性
                    if not all([group_name, member_name, student_id, position]):
                        st.warning(f"Skipping invalid row: Missing required fields")
                        continue
                    
                    # 查找对应群组
                    group = next((g for g in st.session_state.grp_list if g["GroupName"] == group_name), None)
                    if not group:
                        st.warning(f"Skipping: Group '{group_name}' not found")
                        continue
                    
                    # 检查重复（同一群组内学生ID唯一）
                    if any(
                        m["StudentID"] == student_id and m["GroupID"] == group["GroupID"]
                        for m in st.session_state.grp_members
                    ):
                        st.warning(f"Skipping duplicate member: {member_name} (StudentID: {student_id}) in {group_name}")
                        continue
                    
                    # 生成成员ID（M+3位数字，如M001）
                    member_id = f"M{len(st.session_state.grp_members) + 1:03d}"
                    
                    # 添加到成员列表
                    st.session_state.grp_members.append({
                        "MemberID": member_id,
                        "GroupID": group["GroupID"],
                        "GroupName": group_name,  # 冗余存储，便于展示
                        "Name": member_name,
                        "StudentID": student_id,
                        "Position": position,
                        "Contact": contact
                    })
                    
                    # 更新群组成员计数
                    group["MemberCount"] += 1
                    added_count += 1
                
                st.success(f"Successfully imported {added_count} new members!")
        
        except Exception as e:
            st.error(f"Import failed: {str(e)}")

    st.markdown("---")

    # ---------------------- 数据展示区域 ----------------------
    # 1. 群组列表展示
    st.subheader("Groups List")
    if not st.session_state.grp_list:
        st.info("No groups found. Please import groups first.")
    else:
        # 准备群组表格数据
        group_table = [
            {
                "Group ID": g["GroupID"],
                "Group Name": g["GroupName"],
                "Leader": g["Leader"],
                "Description": g["Description"],
                "Member Count": g["MemberCount"]
            }
            for g in st.session_state.grp_list
        ]
        st.dataframe(pd.DataFrame(group_table), use_container_width=True)

    # 2. 成员列表展示
    st.subheader("Group Members")
    if not st.session_state.grp_members:
        st.info("No members found. Please import members first.")
    else:
        # 准备成员表格数据
        member_table = [
            {
                "Member ID": m["MemberID"],
                "Group Name": m["GroupName"],
                "Name": m["Name"],
                "Student ID": m["StudentID"],
                "Position": m["Position"],
                "Contact": m["Contact"]
            }
            for m in st.session_state.grp_members
        ]
        st.dataframe(pd.DataFrame(member_table), use_container_width=True)
