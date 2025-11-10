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

# 解决导入路径问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# 访问码配置（不变）
ACCESS_CODES = {
    "GROUP001": "Group 1", "GROUP002": "Group 2", "GROUP003": "Group 3", "GROUP004": "Group 4",
    "GROUP005": "Group 5", "GROUP006": "Group 6", "GROUP007": "Group 7", "GROUP008": "Group 8"
}

# 图片上传工具类
class DriveUploader:
    def __init__(self):
        self.creds = Credentials.from_service_account_info(
            st.secrets["google_credentials"],
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        self.folder_id = "替换为你的Drive文件夹ID"  # 必须修改

    def upload(self, file_obj, group_code):
        try:
            filename = f"{group_code}_receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
            file_metadata = {
                "name": filename,
                "parents": [self.folder_id],
                "mimeType": file_obj.type
            }
            media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            self.service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"}
            ).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except Exception as e:
            st.error(f"图片上传失败：{str(e)}")
            return None

def render_groups():
    # 初始化会话状态
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:
        st.session_state.current_group_code = None
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录逻辑（修复重运行方法）
    if not st.session_state.group_logged_in:
        st.title("Group Management")
        access_code = st.text_input("Access Code", type="password")
        if st.button("Login"):
            if access_code in ACCESS_CODES:
                st.session_state.group_logged_in = True
                st.session_state.current_group = ACCESS_CODES[access_code]
                st.session_state.current_group_code = access_code
                st.success("Logged in successfully")
                # 关键修复：用最新的 rerun 方法
                st.rerun()  # 替换 st.experimental_rerun()
            else:
                st.error("Invalid access code")
        return

    # 页面标题
    st.title(f"Group: {st.session_state.current_group}")
    if st.button("Logout"):
        st.session_state.group_logged_in = False
        st.rerun()  # 替换 st.experimental_rerun()

    # 连接Google Sheets
    sheet = GoogleSheetHandler().get_sheet("Student", "AllGroupsData")

    # 加载数据
    current_code = st.session_state.current_group_code
    if sheet:
        data = sheet.get_all_records()
        st.session_state.members = [d for d in data if d["group_code"] == current_code and d["data_type"] == "member"]
        st.session_state.incomes = [d for d in data if d["group_code"] == current_code and d["data_type"] == "income"]
        st.session_state.expenses = [d for d in data if d["group_code"] == current_code and d["data_type"] == "expense"]

    # 标签页
    tab1, tab2, tab3 = st.tabs(["Members", "Income", "Reimbursement"])

    # 1. 成员管理（完全保留原功能）
    with tab1:
        st.subheader("Members")
        with st.form("add_member"):
            name = st.text_input("Name")
            student_id = st.text_input("Student ID")
            if st.form_submit_button("Add Member"):
                if name and student_id:
                    member = {
                        "group_code": current_code, "data_type": "member",
                        "uuid": str(uuid.uuid4()), "name": name, "student_id": student_id,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.members.append(member)
                    if sheet:
                        sheet.append_row(list(member.values()))
                    st.success("Member added")
        st.subheader("Member List")
        for member in st.session_state.members:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{member['name']} ({member['student_id']})")
            with col2:
                if st.button("Delete", key=f"del_mem_{member['uuid']}"):
                    st.session_state.members = [m for m in st.session_state.members if m["uuid"] != member["uuid"]]
                    st.success("Member deleted")
                    st.rerun()  # 修复删除后重运行

    # 2. 收入管理（完全保留原功能）
    with tab2:
        st.subheader("Income")
        with st.form("add_income"):
            date = st.date_input("Date")
            amount = st.number_input("Amount", min_value=0.01)
            desc = st.text_input("Description")
            if st.form_submit_button("Add Income"):
                if date and amount and desc:
                    income = {
                        "group_code": current_code, "data_type": "income",
                        "uuid": str(uuid.uuid4()), "date": date.strftime("%Y-%m-%d"),
                        "amount": amount, "description": desc,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.incomes.append(income)
                    if sheet:
                        sheet.append_row(list(income.values()))
                    st.success("Income added")
        st.subheader("Income List")
        for income in st.session_state.incomes:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{income['date']}: ${income['amount']} - {income['description']}")
            with col2:
                if st.button("Delete", key=f"del_inc_{income['uuid']}"):
                    st.session_state.incomes = [i for i in st.session_state.incomes if i["uuid"] != income["uuid"]]
                    st.success("Income deleted")
                    st.rerun()  # 修复删除后重运行

    # 3. 报销管理（新增图片上传）
    with tab3:
        st.subheader("Reimbursement")
        with st.form("add_reimbursement"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", key="exp_date")
                amount = st.number_input("Amount", min_value=0.01, key="exp_amt")
            with col2:
                desc = st.text_input("Description", key="exp_desc")
                receipt = st.file_uploader("Upload Receipt", type=["png", "jpg", "jpeg"], key="exp_receipt")
            
            if st.form_submit_button("Add Reimbursement"):
                if not receipt:
                    st.error("Please upload receipt image")
                    st.stop()
                if date and amount and desc:
                    drive = DriveUploader()
                    receipt_url = drive.upload(receipt, current_code)
                    if not receipt_url:
                        st.error("Failed to upload receipt")
                        st.stop()

                    expense = {
                        "group_code": current_code, "data_type": "expense",
                        "uuid": str(uuid.uuid4()), "date": date.strftime("%Y-%m-%d"),
                        "amount": amount, "description": desc,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "receipt_url": receipt_url
                    }
                    st.session_state.expenses.append(expense)
                    if sheet:
                        sheet.append_row(list(expense.values()))
                    st.success("Reimbursement added with receipt")
                    st.rerun()  # 新增后重运行刷新列表

        st.subheader("Reimbursement List")
        for exp in st.session_state.expenses:
            with st.expander(f"{exp['date']}: ${exp['amount']} - {exp['description']}"):
                if "receipt_url" in exp and exp["receipt_url"]:
                    st.image(exp["receipt_url"], caption="Receipt", use_column_width=True)
                if st.button("Delete", key=f"del_exp_{exp['uuid']}"):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e["uuid"] != exp["uuid"]]
                    st.success("Reimbursement deleted")
                    st.rerun()  # 修复删除后重运行


if __name__ == "__main__":
    render_groups()
