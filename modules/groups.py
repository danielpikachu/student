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

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# 定义允许的访问码及对应群组名称（8个群组）
ACCESS_CODES = {
    "GROUP001": "Group 1",
    "GROUP002": "Group 2",
    "GROUP003": "Group 3",
    "GROUP004": "Group 4",
    "GROUP005": "Group 5",
    "GROUP006": "Group 6",
    "GROUP007": "Group 7",
    "GROUP008": "Group 8"
}

class GoogleDriveHandler:
    """Google Drive 操作工具类，用于上传报销凭证图片"""
    def __init__(self, credentials):
        self.creds = credentials
        self.service = build('drive', 'v3', credentials=self.creds)
        # 替换为你的 Google Drive 文件夹 ID（需手动创建文件夹并获取）
        self.folder_id = "你的文件夹ID"  # 例如："1AbC2dEfG3hIjK4lMnOpQrStUvWxYz"

    def upload_image(self, image_file, group_code):
        """上传图片到指定文件夹并返回可访问链接"""
        filename = f"{group_code}-receipt-{image_file.name}"
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id],
            'mimeType': image_file.type
        }
        media = MediaIoBaseUpload(image_file, mimetype=image_file.type, resumable=True)
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            # 设置为公开可读
            self.service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except HttpError as e:
            st.error(f"Drive API 错误: {str(e)}")
            return None

def render_groups():
    st.set_page_config(page_title="Student Affairs Management", layout="wide")
    
    # 初始化会话状态（记录登录状态、当前群组信息）
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:  # 存储当前群组的访问码（如 GROUP001）
        st.session_state.current_group_code = None
    # 初始化数据存储（成员、收入、支出）
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录界面
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

    # 已登录状态 - 显示群组名称
    st.markdown(f"<h2>📋 Student Affairs Management System - {st.session_state.current_group}</h2>", unsafe_allow_html=True)
    st.caption("Includes three functional modules: member management, income management, and reimbursement management")
    st.divider()

    # 退出/切换群组按钮
    if st.button("Switch Group", key="logout_btn"):
        st.session_state.group_logged_in = False
        st.session_state.current_group = None
        st.session_state.current_group_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.session_state.expenses = []
        st.rerun()

    # 初始化 Google Sheets 连接（单工作表 AllGroupsData）
    sheet_handler = None
    main_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")  # 确保凭证配置正确
        # 连接到现有 Group 文件中的 AllGroupsData 工作表
        main_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",  # Google Sheet 文件名
            worksheet_name="AllGroupsData"  # 工作表名
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
        # 如果工作表不存在，尝试自动创建（确保有权限）
        if "Worksheet not found" in str(e) and sheet_handler:
            with st.spinner("尝试创建 AllGroupsData 工作表..."):
                try:
                    main_sheet = sheet_handler.create_worksheet(
                        spreadsheet_name="Student",
                        worksheet_name="AllGroupsData",
                        rows=1000,
                        cols=20
                    )
                    # 初始化表头行
                    headers = ["group_code", "data_type", "uuid", 
                               "name", "student_id",  # 成员特定字段
                               "date", "amount", "description",  # 收入/报销特定字段
                               "created_at", "receipt_url"]  # 新增：图片链接字段
                    main_sheet.append_row(headers)
                    st.success("AllGroupsData 工作表创建成功！")
                except Exception as e2:
                    st.error(f"创建工作表失败: {str(e2)}")

    # 从单工作表同步当前群组的数据（成员、收入、报销）
    current_code = st.session_state.current_group_code
    if main_sheet and sheet_handler:
        try:
            all_rows = main_sheet.get_all_values()
            if len(all_rows) < 1:
                st.warning("工作表为空，初始化表头...")
                headers = ["group_code", "data_type", "uuid", "name", "student_id", 
                           "date", "amount", "description", "created_at", "receipt_url"]
                main_sheet.append_row(headers)
                all_rows = [headers]
            
            # 解析表头行确定字段索引（避免字段顺序变更导致错误）
            header = all_rows[0]
            col_indices = {col: idx for idx, col in enumerate(header)}
            required_cols = ["group_code", "data_type", "uuid", "created_at"]
            if not all(col in col_indices for col in required_cols):
                st.error("工作表表头格式不正确，请检查字段是否完整")
                return

            # 筛选当前群组的成员数据（data_type=member）
            st.session_state.members = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "name": row[col_indices["name"]],
                    "student_id": row[col_indices["student_id"]]
                }
                for row in all_rows[1:]  # 跳过表头行
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "member"
            ]

            # 筛选当前群组的收入数据（data_type=income）
            st.session_state.incomes = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]]
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "income"
            ]

            # 筛选当前群组的报销数据（data_type=expense）
            st.session_state.expenses = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]],
                    "receipt_url": row[col_indices.get("receipt_url", "")] if "receipt_url" in col_indices else ""
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "expense"
            ]

        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 创建横向标签页
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "💰 Income Management", "🧾 Reimbursement Management"])

    # ---------------------- 成员管理模块（标签页1）----------------------
    with tab1:
        st.markdown("<h3 style='font-size: 16px'>Member Management</h3>", unsafe_allow_html=True)
        st.write("Manage basic information of members (name, student ID)")
        st.divider()

        # 添加新成员
        with st.container():
            st.markdown("**Add New Member**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Member Name*", placeholder="Please enter name")
            with col2:
                student_id = st.text_input("Student ID*", placeholder="Please enter unique ID")
            
            if st.button("Confirm Add Member", use_container_width=True, key="add_member"):
                if not name or not student_id:
                    st.error("Name and Student ID cannot be empty")
                    return
                if any(m["student_id"] == student_id for m in st.session_state.members):
                    st.error(f"Student ID {student_id} already exists")
                    return

                # 生成唯一ID
                member_uuid = str(uuid.uuid4())
                new_member = {
                    "uuid": member_uuid,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                }
                st.session_state.members.append(new_member)

                # 写入Google Sheet（单工作表）
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,  # group_code
                            "member",      # data_type
                            member_uuid,   # uuid
                            name.strip(),  # name
                            student_id.strip(),  # student_id
                            "", "", "",    # 收入/报销字段留空
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # created_at
                            ""  # receipt_url留空
                        ])
                        st.success("Member added successfully")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")

        st.divider()

        # 显示成员列表
        st.markdown("**Member List**", unsafe_allow_html=True)
        if st.session_state.members:
            member_df = pd.DataFrame(st.session_state.members)
            st.dataframe(member_df[["name", "student_id"]], use_container_width=True, hide_index=True)
        else:
            st.info("No members yet, please add members first")

    # ---------------------- 收入管理模块（标签页2）----------------------
    with tab2:
        st.markdown("<h3 style='font-size: 16px'>Income Management</h3>", unsafe_allow_html=True)
        st.write("Record and track all income sources")
        st.divider()

        # 添加新收入
        with st.container():
            st.markdown("**Add New Income**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                income_date = st.date_input("Income Date*")
                income_amount = st.number_input("Amount*", min_value=0.01, step=0.01)
            with col2:
                income_desc = st.text_input("Description*", placeholder="Source of income")
            
            if st.button("Confirm Add Income", use_container_width=True, key="add_income"):
                if not income_date or not income_amount or not income_desc:
                    st.error("Date, Amount, and Description cannot be empty")
                    return

                # 生成唯一ID
                income_uuid = str(uuid.uuid4())
                new_income = {
                    "uuid": income_uuid,
                    "date": income_date.strftime("%Y-%m-%d"),
                    "amount": str(income_amount),
                    "description": income_desc.strip()
                }
                st.session_state.incomes.append(new_income)

                # 写入Google Sheet
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,  # group_code
                            "income",      # data_type
                            income_uuid,   # uuid
                            "", "",        # 成员字段留空
                            new_income["date"],
                            new_income["amount"],
                            new_income["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # created_at
                            ""  # receipt_url留空
                        ])
                        st.success("Income added successfully")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")

        st.divider()

        # 显示收入记录
        st.markdown("**Income Records**", unsafe_allow_html=True)
        if st.session_state.incomes:
            # 计算总收入
            total_income = sum(float(inc["amount"]) for inc in st.session_state.incomes)
            st.markdown(f"**Total Income: ${total_income:.2f}**")
            
            income_df = pd.DataFrame(st.session_state.incomes)
            st.dataframe(income_df[["date", "amount", "description"]], use_container_width=True, hide_index=True)
        else:
            st.info("No income records yet")

    # ---------------------- 报销管理模块（标签页3）----------------------
    with tab3:
        st.markdown("<h3 style='font-size: 16px'>Reimbursement Management</h3>", unsafe_allow_html=True)
        st.write("Record and track reimbursement expenses")
        st.divider()

        # 添加报销记录（含图片上传）
        with st.container():
            st.markdown("**Add New Reimbursement**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                exp_date = st.date_input("Reimbursement Date*")
                exp_amount = st.number_input("Amount*", min_value=0.01, step=0.01)
            with col2:
                exp_desc = st.text_input("Description*", placeholder="Reason for reimbursement")
                # 图片上传
                exp_receipt = st.file_uploader("Upload Receipt (Image)", type=["png", "jpg", "jpeg"])
            
            if st.button("Confirm Add Reimbursement", use_container_width=True, key="add_expense"):
                # 验证图片和必填项
                if not exp_receipt:
                    st.error("Please upload receipt image as proof")
                    return
                if not exp_date or not exp_amount or not exp_desc:
                    st.error("Date, Amount, and Description cannot be empty")
                    return

                # 上传图片到Google Drive
                try:
                    # 使用Streamlit Secrets中的凭证
                    creds = Credentials.from_service_account_info(
                        st.secrets["google_credentials"],
                        scopes=["https://www.googleapis.com/auth/drive"]
                    )
                    drive_handler = GoogleDriveHandler(creds)
                    receipt_url = drive_handler.upload_image(
                        exp_receipt, 
                        st.session_state.current_group_code  # 用群组代码命名，避免重复
                    )
                    if not receipt_url:
                        st.error("Image upload failed")
                        return
                except Exception as e:
                    st.error(f"Image upload error: {str(e)}")
                    return

                # 生成报销记录（包含图片链接）
                exp_uuid = str(uuid.uuid4())
                new_expense = {
                    "uuid": exp_uuid,
                    "date": exp_date.strftime("%Y-%m-%d"),
                    "amount": str(exp_amount),
                    "description": exp_desc.strip(),
                    "receipt_url": receipt_url  # 存储图片链接
                }
                st.session_state.expenses.append(new_expense)

                # 同步到Google Sheet（包含receipt_url列）
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,  # group_code
                            "expense",     # data_type
                            exp_uuid,      # uuid
                            "", "",        # 成员字段留空
                            new_expense["date"],
                            new_expense["amount"],
                            new_expense["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # created_at
                            new_expense["receipt_url"]  # 图片链接
                        ])
                        st.success("Reimbursement added successfully")
                    except Exception as e:
                        st.warning(f"Failed to sync to Sheet: {str(e)}")

        st.divider()

        # 展示报销记录（含图片）
        st.markdown("**Reimbursement Records**", unsafe_allow_html=True)
        if st.session_state.expenses:
            # 计算总报销金额
            total_expense = sum(float(exp["amount"]) for exp in st.session_state.expenses)
            st.markdown(f"**Total Reimbursement: ${total_expense:.2f}**")
            
            for idx, exp in enumerate(st.session_state.expenses, 1):
                with st.expander(f"Reimbursement {idx}: {exp['date']} - ${exp['amount']}"):
                    st.write(f"Description: {exp['description']}")
                    # 显示图片凭证
                    if "receipt_url" in exp and exp["receipt_url"]:
                        st.image(exp["receipt_url"], caption="Receipt Proof", use_column_width=True)
                st.divider()
        else:
            st.info("No reimbursement records yet")
