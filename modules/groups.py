import streamlit as st
import pandas as pd

def render_groups():
    st.header("Groups Management")
    st.write("Import group or member data via file")
    st.divider()

    # 仅保留导入链接对话框
    st.subheader("Import Data from File")
    st.write("Supported formats: .xlsx, .csv")

    # 选择导入类型
    import_type = st.radio(
        "Select data type to import",
        ["Groups", "Members"],
        key="groups_import_type"
    )

    # 文件上传组件
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"],
        key="groups_file_uploader"
    )

    # 导入按钮及处理逻辑
    if st.button("Import Data", key="groups_import_btn", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a file first!")
            return

        try:
            # 读取文件
            if uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)

            # 验证并导入数据
            if import_type == "Groups":
                required_cols = ["GroupName", "Leader"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Groups file must contain columns: {required_cols}")
                    return

                # 初始化会话状态（若不存在）
                if "groups" not in st.session_state:
                    st.session_state.groups = []

                added = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    leader = str(row["Leader"]).strip()
                    description = str(row.get("Description", "")).strip()

                    # 检查重复
                    if group_name and leader and not any(g["GroupName"] == group_name for g in st.session_state.groups):
                        group_id = f"G{len(st.session_state.groups) + 1:03d}"
                        st.session_state.groups.append({
                            "GroupID": group_id,
                            "GroupName": group_name,
                            "Leader": leader,
                            "Description": description,
                            "MemberCount": 0
                        })
                        added += 1

                st.success(f"Successfully imported {added} new groups!")

            else:  # 导入成员
                required_cols = ["GroupName", "Name", "StudentID", "Position"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"Members file must contain columns: {required_cols}")
                    return

                # 初始化会话状态（若不存在）
                if "groups" not in st.session_state:
                    st.session_state.groups = []
                if "group_members" not in st.session_state:
                    st.session_state.group_members = []

                if not st.session_state.groups:
                    st.error("No existing groups. Please create groups first.")
                    return

                added = 0
                for _, row in df.iterrows():
                    group_name = str(row["GroupName"]).strip()
                    name = str(row["Name"]).strip()
                    student_id = str(row["StudentID"]).strip()
                    position = str(row["Position"]).strip()
                    contact = str(row.get("Contact", "")).strip()

                    # 查找对应社团ID
                    group = next((g for g in st.session_state.groups if g["GroupName"] == group_name), None)
                    if not group:
                        st.warning(f"Skipped: Group '{group_name}' not found")
                        continue

                    # 检查重复
                    if name and student_id and position and not any(
                        m["StudentID"] == student_id and m["GroupID"] == group["GroupID"]
                        for m in st.session_state.group_members
                    ):
                        member_id = f"M{len(st.session_state.group_members) + 1:03d}"
                        st.session_state.group_members.append({
                            "MemberID": member_id,
                            "GroupID": group["GroupID"],
                            "Name": name,
                            "StudentID": student_id,
                            "Position": position,
                            "Contact": contact
                        })
                        # 更新成员计数
                        group["MemberCount"] += 1
                        added += 1

                st.success(f"Successfully imported {added} new members!")

        except Exception as e:
            st.error(f"Import failed: {str(e)}")

render_groups()
