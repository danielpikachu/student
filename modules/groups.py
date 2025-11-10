# modules/groups.py
import streamlit as st
import pandas as pd
import uuid
import sys
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 解决导入路径问题（原项目不变）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# 访问码配置（原项目不变）
ACCESS_CODES = {
    "GROUP001": "Group 1", "GROUP002": "Group 2", "GROUP003": "Group 3", "GROUP004": "Group 4",
    "GROUP005": "Group 5", "GROUP006": "Group 6", "GROUP007": "Group 7", "GROUP008": "Group 8"
}

# 仅新增：图片上传工具类
class DriveUploader:
    def __init__(self, credentials_path):
        self.creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        self.folder_id = "替换为你的Drive文件夹ID"  # 必须修改

    def upload(self, file_obj, group_code):
        try:
            filename = f"{group_code}_receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
            file_metadata = {"name": filename, "parents": [self.folder_id], "mimeType": file_obj.type}
            media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            self.service.permissions().create(fileId=file["id"], body={"type": "anyone", "role": "reader"}).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except Exception as e:
            st.error(f"图片上传失败：{str(e)}")
            return None

def render_groups():
    # 会话状态初始化（原项目不变）
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:
        st.session_state.current_group_code = None
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录逻辑（原项目不变）
    if not st.session_state.group_logged_in:
        st.markdown("<h2>📋 Student Affairs Management System</h2>", unsafe_allow_html=True)
        st.caption("Please enter the access code to enter the corresponding group management")
        st.divider()
        access_code = st.text_input("Access Code", placeholder="e.g., GROUP001", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                if access_code in ACCESS_CODES:
                    st.session_state.group_logged_in = True
                    st.session_state.current_group = ACCESS_CODES[access_code]
                    st.session_state.current_group_code = access_code
                    st.success(f"Login successful, welcome to {ACCESS_CODES[access_code]}")
                    st.rerun()
                else:
                    st.error("Invalid access code, please try again")
        with col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.group_logged_in = False
                st.session_state.current_group = None
                st.session_state.current_group_code = None
                st.rerun()
        return

    # 已登录头部（原项目不变）
    st.markdown(f"<h2>📋 Student Affairs Management System - {st.session_state.current_group}</h2>", unsafe_allow_html=True)
    st.caption("Includes three functional modules: member management, income management, and reimbursement management")
    st.divider()
    if st.button("Switch Group", key="logout_btn"):
        st.session_state.group_logged_in = False
        st.session_state.current_group = None
        st.session_state.current_group_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.session_state.expenses = []
        st.rerun()

    # Google Sheets连接（原项目不变）
    CREDENTIALS_PATH = os.path.join(ROOT_DIR, "credentials.json")  # 原项目凭证路径
    sheet_handler = None
    main_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path=CREDENTIALS_PATH)
        main_sheet = sheet_handler.get_worksheet("Student", "AllGroupsData")
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
        if "Worksheet not found" in str(e) and sheet_handler:
            with st.spinner("尝试创建 AllGroupsData 工作表..."):
                try:
                    main_sheet = sheet_handler.create_worksheet("Student", "AllGroupsData", 1000, 20)
                    headers = ["group_code", "data_type", "uuid", "name", "student_id", "date", "amount", "description", "created_at", "receipt_url"]
                    main_sheet.append_row(headers)
                    st.success("AllGroupsData 工作表创建成功！")
                except Exception as e2:
                    st.error(f"创建工作表失败: {str(e2)}")

    # 数据同步（原项目不变，仅报销数据新增receipt_url）
    current_code = st.session_state.current_group_code
    if main_sheet and sheet_handler:
        try:
            all_rows = main_sheet.get_all_values()
            if len(all_rows) < 1:
                all_rows = [["group_code", "data_type", "uuid", "name", "student_id", "date", "amount", "description", "created_at", "receipt_url"]]
                main_sheet.append_row(all_rows[0])
            header = all_rows[0]
            col_indices = {col: idx for idx, col in enumerate(header)}
            # 成员数据（原项目不变）
            st.session_state.members = [
                {"uuid": row[col_indices["uuid"]], "name": row[col_indices["name"]], "student_id": row[col_indices["student_id"]]}
                for row in all_rows[1:] if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "member"
            ]
            # 收入数据（原项目不变）
            st.session_state.incomes = [
                {"uuid": row[col_indices["uuid"]], "date": row[col_indices["date"]], "amount": row[col_indices["amount"]], "description": row[col_indices["description"]]}
                for row in all_rows[1:] if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "income"
            ]
            # 报销数据（新增receipt_url）
            st.session_state.expenses = [
                {"uuid": row[col_indices["uuid"]], "date": row[col_indices["date"]], "amount": row[col_indices["amount"]], "description": row[col_indices["description"]], "receipt_url": row[col_indices.get("receipt_url", "")]}
                for row in all_rows[1:] if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "expense"
            ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 标签页（原项目不变）
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "💰 Income Management", "🧾 Reimbursement Management"])

    # ---------------------- 1. 成员管理（原项目代码完全不变）----------------------
    with tab1:
        st.markdown("<h3 style='font-size: 16px'>Member Management</h3>", unsafe_allow_html=True)
        st.write("Manage basic information of members (name, student ID)")
        st.divider()
        with st.container():
            st.markdown("**Add New Member**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Member Name*", placeholder="Please enter name")
            with col2:
                student_id = st.text_input("Student ID*", placeholder="Please enter unique ID")
            if st.button("Confirm Add Member", use_container_width=True):
                if not name or not student_id:
                    st.error("Name and Student ID cannot be empty")
                    return
                if any(m["student_id"] == student_id for m in st.session_state.members):
                    st.error(f"Student ID {student_id} already exists")
                    return
                member_uuid = str(uuid.uuid4())
                new_member = {"uuid": member_uuid, "name": name.strip(), "student_id": student_id.strip()}
                st.session_state.members.append(new_member)
                if main_sheet:
                    try:
                        main_sheet.append_row([current_code, "member", member_uuid, name.strip(), student_id.strip(), "", "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""])
                        st.success("Member added successfully")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")
        st.divider()
        st.markdown("**Member List**", unsafe_allow_html=True)
        if st.session_state.members:
            member_df = pd.DataFrame(st.session_state.members)
            for idx, row in member_df.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{row['name']}** ({row['student_id']})")
                with col2:
                    if st.button("Delete", key=f"del_member_{row['uuid']}"):
                        st.session_state.members = [m for m in st.session_state.members if m["uuid"] != row["uuid"]]
                        st.success("Member deleted successfully")
                        st.rerun()
        else:
            st.info("No members yet, please add members first")

    # ---------------------- 2. 收入管理（原项目代码完全不变）----------------------
    with tab2:
        st.markdown("<h3 style='font-size: 16px'>Income Management</h3>", unsafe_allow_html=True)
        st.write("Record and track all income sources")
        st.divider()
        with st.container():
            st.markdown("**Add New Income**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                income_date = st.date_input("Income Date*")
                income_amount = st.number_input("Amount*", min_value=0.01, step=0.01)
            with col2:
                income_desc = st.text_input("Description*", placeholder="Source of income")
            if st.button("Confirm Add Income", use_container_width=True):
                if not income_date or not income_amount or not income_desc:
                    st.error("Date, Amount, and Description cannot be empty")
                    return
                income_uuid = str(uuid.uuid4())
                new_income = {"uuid": income_uuid, "date": income_date.strftime("%Y-%m-%d"), "amount": str(income_amount), "description": income_desc.strip()}
                st.session_state.incomes.append(new_income)
                if main_sheet:
                    try:
                        main_sheet.append_row([current_code, "income", income_uuid, "", "", new_income["date"], new_income["amount"], new_income["description"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""])
                        st.success("Income added successfully")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")
        st.divider()
        st.markdown("**Income Records**", unsafe_allow_html=True)
        if st.session_state.incomes:
            total_income = sum(float(inc["amount"]) for inc in st.session_state.incomes)
            st.markdown(f"**Total Income: ${total_income:.2f}**")
            for idx, inc in enumerate(st.session_state.incomes):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{inc['date']}** - ${inc['amount']}: {inc['description']}")
                with col2:
                    if st.button("Delete", key=f"del_income_{inc['uuid']}"):
                        st.session_state.incomes = [i for i in st.session_state.incomes if i["uuid"] != inc["uuid"]]
                        st.success("Income deleted successfully")
                        st.rerun()
        else:
            st.info("No income records yet")

    # ---------------------- 3. 报销管理（仅新增图片上传功能）----------------------
    with tab3:
        st.markdown("<h3 style='font-size: 16px'>Reimbursement Management</h3>", unsafe_allow_html=True)
        st.write("Record and track reimbursement expenses with receipt")
        st.divider()

        # 新增报销（添加图片上传）
        with st.container():
            st.markdown("**Add New Reimbursement**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Reimbursement Date*", key="exp_date")
                exp_amount = st.number_input("Amount*", min_value=0.01, step=0.01, key="exp_amount")
            with col2:
                exp_desc = st.text_input("Description*", placeholder="Reason for reimbursement", key="exp_desc")
                # 新增：图片上传组件
                exp_receipt = st.file_uploader("Upload Receipt (Image)", type=["png", "jpg", "jpeg"], key="exp_receipt")
            
            if st.button("Confirm Add Reimbursement", use_container_width=True, key="add_expense"):
                # 新增：验证图片
                if not exp_receipt:
                    st.error("Please upload receipt image as proof")
                    return
                if not exp_date or not exp_amount or not exp_desc:
                    st.error("Date, Amount, and Description cannot be empty")
                    return

                # 新增：上传图片到Drive
                try:
                    drive = DriveUploader(credentials_path=CREDENTIALS_PATH)
                    receipt_url = drive.upload(exp_receipt, current_code)
                    if not receipt_url:
                        st.error("Image upload failed")
                        return
                except Exception as e:
                    st.error(f"Image upload error: {str(e)}")
                    return

                # 原有逻辑（新增receipt_url）
                exp_uuid = str(uuid.uuid4())
                new_expense = {
                    "uuid": exp_uuid, "date": exp_date.strftime("%Y-%m-%d"), 
                    "amount": str(exp_amount), "description": exp_desc.strip(), 
                    "receipt_url": receipt_url  # 新增字段
                }
                st.session_state.expenses.append(new_expense)

                # 同步到Sheet（含图片链接）
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code, "expense", exp_uuid, "", "",
                            new_expense["date"], new_expense["amount"], new_expense["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), receipt_url
                        ])
                        st.success("Reimbursement added successfully with receipt")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")

        st.divider()

        # 报销记录展示（含图片和删除功能）
        st.markdown("**Reimbursement Records**", unsafe_allow_html=True)
        if st.session_state.expenses:
            total_expense = sum(float(exp["amount"]) for exp in st.session_state.expenses)
            st.markdown(f"**Total Reimbursement: ${total_expense:.2f}**")
            for idx, exp in enumerate(st.session_state.expenses, 1):
                with st.expander(f"Reimbursement {idx}: {exp['date']} - ${exp['amount']}"):
                    st.write(f"Description: {exp['description']}")
                    # 新增：显示图片
                    if "receipt_url" in exp and exp["receipt_url"]:
                        st.image(exp["receipt_url"], caption="Receipt Proof", use_column_width=True)
                    # 保留删除功能
                    if st.button("Delete", key=f"del_expense_{exp['uuid']}"):
                        st.session_state.expenses = [e for e in st.session_state.expenses if e["uuid"] != exp["uuid"]]
                        st.success("Reimbursement deleted successfully")
                        st.rerun()
        else:
            st.info("No reimbursement records yet")


if __name__ == "__main__":
    render_groups()
