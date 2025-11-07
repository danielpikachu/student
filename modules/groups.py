import streamlit as st
import pandas as pd

def render_groups():
    """渲染群组模块界面（grp_前缀命名空间）"""
    st.header("👥 Groups Management")
    st.write("Import and manage member data")
    st.divider()

    # ---------------------- 数据导入区域 ----------------------
    st.subheader("Import Member Data from File")
    st.write("Supported formats: .xlsx, .csv")
    
    # 文件上传组件
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"],
        key="grp_upload_file"  # 层级化Key：grp_模块_上传组件_文件
    )
    
    # 导入按钮
    if st.button("Import Members", key="grp_btn_import", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a file first!")
            return
        
        try:
            # 读取文件
            if uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
            else:  # CSV格式
                df = pd.read_csv(uploaded_file)
            
            # 验证必要列
            required_cols = ["GroupName", "Name", "StudentID", "Position"]
            if not all(col in df.columns for col in required_cols):
                st.error(f"Members file must contain columns: {', '.join(required_cols)}")
                return
            
            # 初始化群组列表（如果不存在）
            if "grp_list" not in st.session_state:
                st.session_state.grp_list = []
            
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
                
                # 查找对应群组，如果不存在则自动创建
                group = next((g for g in st.session_state.grp_list if g["GroupName"] == group_name), None)
                if not group:
                    # 生成新群组ID
                    group_id = f"G{len(st.session_state.grp_list) + 1:03d}"
                    # 创建新群组（Leader暂时留空或使用默认值）
                    group = {
                        "GroupID": group_id,
                        "GroupName": group_name,
                        "Leader": "Not specified",  # 自动创建时默认值
                        "Description": "",
                        "MemberCount": 0
                    }
                    st.session_state.grp_list.append(group)
                    st.info(f"Auto-created group: {group_name} (since it didn't exist)")
                
                # 检查重复（同一群组内学生ID唯一）
                if any(
                    m["StudentID"] == student_id and m["GroupID"] == group["GroupID"]
                    for m in st.session_state.grp_members
                ):
                    st.warning(f"Skipping duplicate member: {member_name} (StudentID: {student_id}) in {group_name}")
                    continue
                
                # 初始化成员列表（如果不存在）
                if "grp_members" not in st.session_state:
                    st.session_state.grp_members = []
                
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
    # 1. 群组列表展示（由成员数据自动生成）
    st.subheader("Groups List")
    if not st.session_state.get("grp_list", []):
        st.info("No groups found. Import members to create groups.")
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
    if not st.session_state.get("grp_members", []):
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
