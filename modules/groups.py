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
from googleapiclient.errors import HttpError

# 解决根目录导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# 原有访问码配置（保持不变）
ACCESS_CODES = {
    "GROUP001": "Group 1", "GROUP002": "Group 2", "GROUP003": "Group 3", "GROUP004": "Group 4",
    "GROUP005": "Group 5", "GROUP006": "Group 6", "GROUP007": "Group 7", "GROUP008": "Group 8"
}

# 新增：Google Drive图片上传工具类（独立于原有逻辑）
class GoogleDriveHandler:
    def __init__(self, credentials):
        self.creds = credentials
        self.service = build('drive', 'v3', credentials=self.creds)
        self.folder_id = "替换为你的Drive文件夹ID"  # 仅需修改这里

    def upload_image(self, image_file, group_code):
        filename = f"{group_code}-receipt-{datetime.now().strftime('%Y%m%d%H%M%S')}-{image_file.name}"
        file_metadata = {'name': filename, 'parents': [self.folder_id], 'mimeType': image_file.type}
        media = MediaIoBaseUpload(image_file, mimetype=image_file.type, resumable=True)
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            self.service.permissions().create(fileId=file['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except Exception as e:
            st.error(f"图片上传失败: {str(e)}")
            return None

def render_groups():
    st.set_page_config(page_title="Student Affairs Management", layout="wide")
    
    # 原有会话状态初始化（完全保留）
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:
        st.session_state.current_group_code = None
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录逻辑（完全保留原功能）
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

    # 已登录状态头部（保留原功能）
    st.markdown(f"<h2>📋 {st.session_state.current_group}</h2>", unsafe_allow_html=True)
    st.caption("Manage group members, income and expenses")
    st.divider()

    if st.button("Switch Group"):
        st.session_state.group_logged_in = False
        st.session_state.current_group = None
        st.session_state.current_group_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.session_state.expenses = []
        st.rerun()

    # Google Sheets连接（保留原逻辑）
    sheet_handler = None
    main_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        main_sheet = sheet_handler.get_worksheet("Student", "AllGroupsData")
    except Exception as e:
        st.error(f"Sheets初始化失败: {str(e)}")
        if "Worksheet not found" in str(e) and sheet_handler:
            with st.spinner("创建工作表..."):
                try:
                    main_sheet = sheet_handler.create_worksheet("Student", "AllGroupsData", 1000, 20)
                    main_sheet.append_row(["group_code", "data_type", "uuid", "name", "student_id", 
                                         "date", "amount", "description", "created_at", "receipt_url"])
                    st.success("工作表创建成功")
                except Exception as e2:
                    st.error(f"创建失败: {str(e2)}")

    # 数据同步（保留原逻辑，仅新增receipt_url字段同步）
    current_code = st.session_state.current_group_code
    if main_sheet and sheet_handler:
        try:
            all_rows = main_sheet.get_all_values()
            if len(all_rows) < 1:
                all_rows = [["group_code", "data_type", "uuid", "name", "student_id", 
                           "date", "amount", "description", "created_at", "receipt_url"]]
                main_sheet.append_row(all_rows[0])
            
            header = all_rows[0]
            col_indices = {col: idx for idx, col in enumerate(header)}
            
            # 成员数据（完全保留）
            st.session_state.members = [
                {"uuid": row[col_indices["uuid"]], "name": row[col_indices["name"]], 
                 "student_id": row[col_indices["student_id"]]}
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "member"
            ]

            # 收入数据（完全保留）
            st.session_state.incomes = [
                {"uuid": row[col_indices["uuid"]], "date": row[col_indices["date"]], 
                 "amount": row[col_indices["amount"]], "description": row[col_indices["description"]]}
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "income"
            ]

            # 报销数据（新增receipt_url同步）
            st.session_state.expenses = [
                {"uuid": row[col_indices["uuid"]], "date": row[col_indices["date"]], 
                 "amount": row[col_indices["amount"]], "description": row[col_indices["description"]],
                 "receipt_url": row[col_indices["receipt_url"]] if "receipt_url" in col_indices else ""}
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code and row[col_indices["data_type"]] == "expense"
            ]

        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 标签页（保留原结构）
    tab1, tab2, tab3 = st.tabs(["👥 Members", "💰 Income", "🧾 Reimbursement"])

    # 1. 成员管理（完全保留原功能，包括删除按钮）
    with tab1:
        st.subheader("Member Management")
        st.write("Add and manage group members")
        st.divider()

        # 添加成员（原逻辑）
        with st.expander("Add New Member"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name", key="member_name")
            with col2:
                student_id = st.text_input("Student ID", key="member_id")
            if st.button("Add Member", key="add_member"):
                if name and student_id and not any(m["student_id"] == student_id for m in st.session_state.members):
                    member_uuid = str(uuid.uuid4())
                    st.session_state.members.append({"uuid": member_uuid, "name": name, "student_id": student_id})
                    if main_sheet:
                        main_sheet.append_row([current_code, "member", member_uuid, name, student_id, "", "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""])
                    st.success("Member added")
                else:
                    st.error("Invalid input or duplicate ID")

        # 成员列表（保留删除功能）
        st.subheader("Member List")
        if st.session_state.members:
            member_df = pd.DataFrame(st.session_state.members)
            for idx, row in member_df.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{row['name']}** ({row['student_id']})")
                with col2:
                    if st.button("Delete", key=f"del_member_{row['uuid']}"):
                        st.session_state.members = [m for m in st.session_state.members if m["uuid"] != row["uuid"]]
                        st.success("Member deleted")
                        st.rerun()
        else:
            st.info("No members yet")

    # 2. 收入管理（完全保留原功能，包括删除按钮）
    with tab2:
        st.subheader("Income Management")
        st.write("Record and track income")
        st.divider()

        # 添加收入（原逻辑）
        with st.expander("Add New Income"):
            col1, col2 = st.columns(2)
            with col1:
                income_date = st.date_input("Date", key="income_date")
                income_amount = st.number_input("Amount", min_value=0.01, key="income_amt")
            with col2:
                income_desc = st.text_input("Description", key="income_desc")
            if st.button("Add Income", key="add_income"):
                if income_date and income_amount and income_desc:
                    income_uuid = str(uuid.uuid4())
                    st.session_state.incomes.append({
                        "uuid": income_uuid, "date": income_date.strftime("%Y-%m-%d"),
                        "amount": str(income_amount), "description": income_desc
                    })
                    if main_sheet:
                        main_sheet.append_row([current_code, "income", income_uuid, "", "", 
                                             income_date.strftime("%Y-%m-%d"), str(income_amount), 
                                             income_desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""])
                    st.success("Income added")
                else:
                    st.error("Please fill all fields")

        # 收入列表（保留删除功能）
        st.subheader("Income Records")
        if st.session_state.incomes:
            total_income = sum(float(inc["amount"]) for inc in st.session_state.incomes)
            st.write(f"**Total Income: ${total_income:.2f}**")
            for idx, inc in enumerate(st.session_state.incomes):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"**{inc['date']}** - ${inc['amount']}: {inc['description']}")
                with col2:
                    if st.button("Delete", key=f"del_income_{inc['uuid']}"):
                        st.session_state.incomes = [i for i in st.session_state.incomes if i["uuid"] != inc["uuid"]]
                        st.success("Income deleted")
                        st.rerun()
        else:
            st.info("No income records")

    # 3. 报销管理（仅新增图片上传功能，保留原有删除和表格）
    with tab3:
        st.subheader("Reimbursement Management")
        st.write("Record and track reimbursements with receipts")
        st.divider()

        # 添加报销（新增图片上传）
        with st.expander("Add New Reimbursement"):
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Date", key="exp_date")
                exp_amount = st.number_input("Amount", min_value=0.01, key="exp_amt")
            with col2:
                exp_desc = st.text_input("Description", key="exp_desc")
                # 新增：图片上传组件
                exp_receipt = st.file_uploader("Upload Receipt (Image)", type=["png", "jpg", "jpeg"], key="exp_receipt")
            
            if st.button("Add Reimbursement", key="add_expense"):
                # 新增：验证图片
                if not exp_receipt:
                    st.error("Please upload receipt image")
                    return
                if exp_date and exp_amount and exp_desc:
                    # 新增：上传图片到Drive
                    try:
                        creds = Credentials.from_service_account_info(
                            st.secrets["google_credentials"],
                            scopes=["https://www.googleapis.com/auth/drive"]
                        )
                        drive_handler = GoogleDriveHandler(creds)
                        receipt_url = drive_handler.upload_image(
                            exp_receipt, 
                            st.session_state.current_group_code
                        )
                        if not receipt_url:
                            st.error("Failed to upload image")
                            return
                    except Exception as e:
                        st.error(f"Image upload error: {str(e)}")
                        return

                    # 原有报销记录逻辑（新增receipt_url）
                    exp_uuid = str(uuid.uuid4())
                    new_expense = {
                        "uuid": exp_uuid, "date": exp_date.strftime("%Y-%m-%d"),
                        "amount": str(exp_amount), "description": exp_desc,
                        "receipt_url": receipt_url  # 新增字段
                    }
                    st.session_state.expenses.append(new_expense)

                    # 同步到Sheet（新增receipt_url列）
                    if main_sheet:
                        main_sheet.append_row([
                            current_code, "expense", exp_uuid, "", "",
                            exp_date.strftime("%Y-%m-%d"), str(exp_amount), exp_desc,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), receipt_url
                        ])
                    st.success("Reimbursement added with receipt")
                else:
                    st.error("Please fill all fields")

        # 报销列表（保留删除功能，新增图片显示）
        st.subheader("Reimbursement Records")
        if st.session_state.expenses:
            total_exp = sum(float(exp["amount"]) for exp in st.session_state.expenses)
            st.write(f"**Total Reimbursement: ${total_exp:.2f}**")
            for idx, exp in enumerate(st.session_state.expenses):
                with st.expander(f"Reimbursement {idx+1}: {exp['date']} - ${exp['amount']}"):
                    st.write(f"Description: {exp['description']}")
                    # 新增：显示图片
                    if "receipt_url" in exp and exp["receipt_url"]:
                        st.image(exp["receipt_url"], caption="Receipt", use_column_width=True)
                    # 保留删除按钮
                    if st.button("Delete", key=f"del_exp_{exp['uuid']}"):
                        st.session_state.expenses = [e for e in st.session_state.expenses if e["uuid"] != exp["uuid"]]
                        st.success("Reimbursement deleted")
                        st.rerun()
        else:
            st.info("No reimbursement records")
