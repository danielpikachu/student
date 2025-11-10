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

# 解决导入路径问题（与原项目一致）
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler  # 原项目的Sheets工具类

# 原项目的访问码配置（完全不变）
ACCESS_CODES = {
    "GROUP001": "Group 1", "GROUP002": "Group 2", "GROUP003": "Group 3", "GROUP004": "Group 4",
    "GROUP005": "Group 5", "GROUP006": "Group 6", "GROUP007": "Group 7", "GROUP008": "Group 8"
}

# 仅新增：图片上传到Google Drive的工具类（独立逻辑，不影响原有代码）
class DriveUploader:
    def __init__(self):
        # 使用原项目的凭证配置
        self.creds = Credentials.from_service_account_info(
            st.secrets["google_credentials"],
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        # ********** 必须修改为你的Drive文件夹ID **********
        self.folder_id = "替换为你的Drive文件夹ID"  # 例如："1a2b3c4d5e6f7g8h9i0j"

    def upload(self, file_obj, group_code):
        """上传图片并返回可访问链接"""
        try:
            # 生成唯一文件名（避免重复）
            filename = f"{group_code}_receipt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_obj.name}"
            # 上传配置
            file_metadata = {
                "name": filename,
                "parents": [self.folder_id],  # 上传到指定文件夹
                "mimeType": file_obj.type
            }
            # 执行上传
            media = MediaIoBaseUpload(file_obj, mimetype=file_obj.type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            # 设置公开访问（确保Streamlit能显示）
            self.service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"}
            ).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except Exception as e:
            st.error(f"图片上传失败：{str(e)}")
            return None

def render_groups():
    # 原项目的会话状态初始化（完全保留）
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:
        st.session_state.current_group_code = None
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录逻辑（与原项目完全一致）
    if not st.session_state.group_logged_in:
        st.title("Group Management")
        access_code = st.text_input("Access Code", type="password")
        if st.button("Login"):
            if access_code in ACCESS_CODES:
                st.session_state.group_logged_in = True
                st.session_state.current_group = ACCESS_CODES[access_code]
                st.session_state.current_group_code = access_code
                st.success("Logged in successfully")
                st.experimental_rerun()
            else:
                st.error("Invalid access code")
        return

    # 页面标题（与原项目一致）
    st.title(f"Group: {st.session_state.current_group}")
    if st.button("Logout"):
        st.session_state.group_logged_in = False
        st.experimental_rerun()

    # 连接Google Sheets（使用原项目的逻辑）
    sheet = GoogleSheetHandler().get_sheet("Student", "AllGroupsData")

    # 加载数据（仅在报销数据中新增receipt_url字段）
    current_code = st.session_state.current_group_code
    if sheet:
        data = sheet.get_all_records()
        # 成员数据（完全不变）
        st.session_state.members = [d for d in data if d["group_code"] == current_code and d["data_type"] == "member"]
        # 收入数据（完全不变）
        st.session_state.incomes = [d for d in data if d["group_code"] == current_code and d["data_type"] == "income"]
        # 报销数据（新增receipt_url字段）
        st.session_state.expenses = [d for d in data if d["group_code"] == current_code and d["data_type"] == "expense"]

    # 标签页（与原项目一致）
    tab1, tab2, tab3 = st.tabs(["Members", "Income", "Reimbursement"])

    # 1. 成员管理（完全保留原项目代码）
    with tab1:
        st.subheader("Members")
        # 添加成员（原逻辑）
        with st.form("add_member"):
            name = st.text_input("Name")
            student_id = st.text_input("Student ID")
            if st.form_submit_button("Add Member"):
                if name and student_id:
                    member = {
                        "group_code": current_code,
                        "data_type": "member",
                        "uuid": str(uuid.uuid4()),
                        "name": name,
                        "student_id": student_id,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.members.append(member)
                    if sheet:
                        sheet.append_row(list(member.values()))
                    st.success("Member added")
        # 显示成员（原逻辑，含删除）
        st.subheader("Member List")
        for member in st.session_state.members:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{member['name']} ({member['student_id']})")
            with col2:
                if st.button("Delete", key=f"del_mem_{member['uuid']}"):
                    st.session_state.members = [m for m in st.session_state.members if m["uuid"] != member["uuid"]]
                    # 原项目的删除同步逻辑（如有）
                    st.success("Member deleted")

    # 2. 收入管理（完全保留原项目代码）
    with tab2:
        st.subheader("Income")
        # 添加收入（原逻辑）
        with st.form("add_income"):
            date = st.date_input("Date")
            amount = st.number_input("Amount", min_value=0.01)
            desc = st.text_input("Description")
            if st.form_submit_button("Add Income"):
                if date and amount and desc:
                    income = {
                        "group_code": current_code,
                        "data_type": "income",
                        "uuid": str(uuid.uuid4()),
                        "date": date.strftime("%Y-%m-%d"),
                        "amount": amount,
                        "description": desc,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.incomes.append(income)
                    if sheet:
                        sheet.append_row(list(income.values()))
                    st.success("Income added")
        # 显示收入（原逻辑，含删除）
        st.subheader("Income List")
        for income in st.session_state.incomes:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{income['date']}: ${income['amount']} - {income['description']}")
            with col2:
                if st.button("Delete", key=f"del_inc_{income['uuid']}"):
                    st.session_state.incomes = [i for i in st.session_state.incomes if i["uuid"] != income["uuid"]]
                    # 原项目的删除同步逻辑（如有）
                    st.success("Income deleted")

    # 3. 报销管理（仅在此处新增图片上传功能）
    with tab3:
        st.subheader("Reimbursement")
        # 添加报销（新增图片上传）
        with st.form("add_reimbursement"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", key="exp_date")
                amount = st.number_input("Amount", min_value=0.01, key="exp_amt")
            with col2:
                desc = st.text_input("Description", key="exp_desc")
                # 新增：图片上传框
                receipt = st.file_uploader("Upload Receipt", type=["png", "jpg", "jpeg"], key="exp_receipt")
            
            # 提交按钮（原逻辑+图片验证）
            if st.form_submit_button("Add Reimbursement"):
                # 新增：验证图片是否上传
                if not receipt:
                    st.error("Please upload receipt image")
                    st.stop()
                # 原逻辑：验证其他字段
                if date and amount and desc:
                    # 新增：上传图片到Drive
                    drive = DriveUploader()
                    receipt_url = drive.upload(receipt, current_code)
                    if not receipt_url:
                        st.error("Failed to upload receipt")
                        st.stop()

                    # 原逻辑：创建报销记录（新增receipt_url字段）
                    expense = {
                        "group_code": current_code,
                        "data_type": "expense",
                        "uuid": str(uuid.uuid4()),
                        "date": date.strftime("%Y-%m-%d"),
                        "amount": amount,
                        "description": desc,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "receipt_url": receipt_url  # 新增字段
                    }
                    st.session_state.expenses.append(expense)
                    # 同步到Sheet（新增receipt_url）
                    if sheet:
                        sheet.append_row(list(expense.values()))
                    st.success("Reimbursement added with receipt")

        # 显示报销记录（新增图片显示，保留删除）
        st.subheader("Reimbursement List")
        for exp in st.session_state.expenses:
            with st.expander(f"{exp['date']}: ${exp['amount']} - {exp['description']}"):
                # 新增：显示图片
                if "receipt_url" in exp and exp["receipt_url"]:
                    st.image(exp["receipt_url"], caption="Receipt", use_column_width=True)
                # 保留删除按钮
                if st.button("Delete", key=f"del_exp_{exp['uuid']}"):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e["uuid"] != exp["uuid"]]
                    # 原项目的删除同步逻辑（如有）
                    st.success("Reimbursement deleted")


# 原项目的入口调用（保持不变）
if __name__ == "__main__":
    render_groups()
