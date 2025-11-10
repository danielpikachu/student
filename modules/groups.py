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

# 访问码配置（不变）
ACCESS_CODES = {
    "GROUP001": "Group 1", "GROUP002": "Group 2", "GROUP003": "Group 3", "GROUP004": "Group 4",
    "GROUP005": "Group 5", "GROUP006": "Group 6", "GROUP007": "Group 7", "GROUP008": "Group 8"
}

# 图片上传工具类（独立逻辑）
class DriveUploader:
    def __init__(self):
        # 使用原项目的凭证配置方式
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
    # 初始化会话状态（与原项目一致）
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:
        st.session_state.current_group_code = None
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录逻辑（修复重运行）
    if not st.session_state.group_logged_in:
        st.title("Group Management")
        access_code = st.text_input("Access Code", type="password")
        if st.button("Login"):
            if access_code in ACCESS_CODES:
                st.session_state.group_logged_in = True
                st.session_state.current_group = ACCESS_CODES[access_code]
                st.session_state.current_group_code = access_code
                st.success("Logged in successfully")
                st.rerun()  # 正确的重运行方法
            else:
                st.error("Invalid access code")
        return

    # 页面标题
    st.title(f"Group: {st.session_state.current_group}")
    if st.button("Logout"):
        st.session_state.group_logged_in = False
        st.rerun()

    # 修复核心错误：按原项目方式初始化GoogleSheetHandler
    # 原项目中GoogleSheetHandler可能需要凭证路径或无参初始化
    try:
        # 尝试原项目的初始化方式（无参数）
        sheet_handler = GoogleSheetHandler()
        # 按原项目方法获取工作表（可能是get_worksheet而非get_sheet）
        sheet = sheet_handler.get_worksheet("Student", "AllGroupsData")
    except Exception as e:
        st.error(f"无法连接Google Sheets：{str(e)}")
        sheet = None

    # 加载数据（与原项目逻辑一致）
    current_code = st.session_state.current_group_code
    if sheet:
        try:
            # 原项目可能使用get_all_values()而非get_all_records()
            all_values = sheet.get_all_values()
            if len(all_values) < 2:  # 表头+至少一行数据
                st.session_state.members = []
                st.session_state.incomes = []
                st.session_state.expenses = []
            else:
                # 解析表头和数据（原项目的字段顺序）
                headers = all_values[0]
                data = [dict(zip(headers, row)) for row in all_values[1:]]
                st.session_state.members = [d for d in data if d["group_code"] == current_code and d["data_type"] == "member"]
                st.session_state.incomes = [d for d in data if d["group_code"] == current_code and d["data_type"] == "income"]
                st.session_state.expenses = [d for d in data if d["group_code"] == current_code and d["data_type"] == "expense"]
        except Exception as e:
            st.warning(f"数据加载失败：{str(e)}")

    # 标签页（与原项目一致）
    tab1, tab2, tab3 = st.tabs(["Members", "Income", "Reimbursement"])

    # 1. 成员管理（完全保留原功能）
    with tab1:
        st.subheader("Members")
        with st.form("add_member"):
            name = st.text_input("Name")
            student_id = st.text_input("Student ID")
            if st.form_submit_button("Add Member"):
                if name and student_id:
                    member_uuid = str(uuid.uuid4())
                    member_data = [
                        current_code, "member", member_uuid,
                        name, student_id, "", "", "",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""
                    ]
                    st.session_state.members.append({
                        "group_code": current_code, "data_type": "member", "uuid": member_uuid,
                        "name": name, "student_id": student_id
                    })
                    if sheet:
                        sheet.append_row(member_data)
                    st.success("Member added")
                    st.rerun()
        st.subheader("Member List")
        for member in st.session_state.members:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{member['name']} ({member['student_id']})")
            with col2:
                if st.button("Delete", key=f"del_mem_{member['uuid']}"):
                    st.session_state.members = [m for m in st.session_state.members if m["uuid"] != member["uuid"]]
                    st.success("Member deleted")
                    st.rerun()

    # 2. 收入管理（完全保留原功能）
    with tab2:
        st.subheader("Income")
        with st.form("add_income"):
            date = st.date_input("Date")
            amount = st.number_input("Amount", min_value=0.01)
            desc = st.text_input("Description")
            if st.form_submit_button("Add Income"):
                if date and amount and desc:
                    income_uuid = str(uuid.uuid4())
                    income_data = [
                        current_code, "income", income_uuid,
                        "", "", date.strftime("%Y-%m-%d"),
                        str(amount), desc,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""
                    ]
                    st.session_state.incomes.append({
                        "group_code": current_code, "data_type": "income", "uuid": income_uuid,
                        "date": date.strftime("%Y-%m-%d"), "amount": str(amount), "description": desc
                    })
                    if sheet:
                        sheet.append_row(income_data)
                    st.success("Income added")
                    st.rerun()
        st.subheader("Income List")
        for income in st.session_state.incomes:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"{income['date']}: ${income['amount']} - {income['description']}")
            with col2:
                if st.button("Delete", key=f"del_inc_{income['uuid']}"):
                    st.session_state.incomes = [i for i in st.session_state.incomes if i["uuid"] != income["uuid"]]
                    st.success("Income deleted")
                    st.rerun()

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
                    # 上传图片
                    drive = DriveUploader()
                    receipt_url = drive.upload(receipt, current_code)
                    if not receipt_url:
                        st.error("Failed to upload receipt")
                        st.stop()

                    # 保存报销记录
                    exp_uuid = str(uuid.uuid4())
                    exp_data = [
                        current_code, "expense", exp_uuid,
                        "", "", date.strftime("%Y-%m-%d"),
                        str(amount), desc,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        receipt_url  # 新增图片链接
                    ]
                    st.session_state.expenses.append({
                        "group_code": current_code, "data_type": "expense", "uuid": exp_uuid,
                        "date": date.strftime("%Y-%m-%d"), "amount": str(amount),
                        "description": desc, "receipt_url": receipt_url
                    })
                    if sheet:
                        sheet.append_row(exp_data)
                    st.success("Reimbursement added with receipt")
                    st.rerun()

        # 显示报销记录（含图片）
        st.subheader("Reimbursement List")
        for exp in st.session_state.expenses:
            with st.expander(f"{exp['date']}: ${exp['amount']} - {exp['description']}"):
                if "receipt_url" in exp and exp["receipt_url"]:
                    st.image(exp["receipt_url"], caption="Receipt", use_column_width=True)
                if st.button("Delete", key=f"del_exp_{exp['uuid']}"):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e["uuid"] != exp["uuid"]]
                    st.success("Reimbursement deleted")
                    st.rerun()


if __name__ == "__main__":
    render_groups()
