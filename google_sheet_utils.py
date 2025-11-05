# google_sheet_utils.py
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st 

class GoogleSheetHandler:
    """Google Sheets 操作工具类，封装认证和工作表操作"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        # 默认可用权限：读写工作表
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()  # 初始化时完成授权

    def _authorize(self):
        """认证逻辑：优先从Streamlit Secrets读取，其次从本地文件读取"""
        try:
            # 1. 尝试从Streamlit Secrets获取凭证（云端部署）
            if "google_credentials" in st.secrets:
                creds_dict = st.secrets["google_credentials"]
                return Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            
            # 2. 尝试从本地文件获取凭证（本地开发）
            if self.credentials_path and os.path.exists(self.credentials_path):
                return Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
            
            # 3. 认证失败
            raise Exception("No valid credentials found. Check Streamlit Secrets or local credentials file.")
        
        except Exception as e:
            st.error(f"Google Sheets 认证失败：{str(e)}")
            raise

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """获取指定表格中的指定工作表"""
        try:
            # 打开表格
            spreadsheet = self.client.open(spreadsheet_name)
            # 获取工作表
            return spreadsheet.worksheet(worksheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except gspread.WorksheetNotFound:
            raise Exception(f"Worksheet not found: {worksheet_name}")
        except Exception as e:
            raise Exception(f"Failed to get worksheet: {str(e)}")

    def get_all_records(self, worksheet):
        """获取工作表所有记录（字典列表格式）"""
        try:
            return worksheet.get_all_records()
        except Exception as e:
            raise Exception(f"Failed to get records: {str(e)}")

    def append_record(self, worksheet, data):
        """向工作表追加一行记录"""
        try:
            worksheet.append_row(data)
        except Exception as e:
            raise Exception(f"Failed to append record: {str(e)}")

    def delete_record_by_value(self, worksheet, value, column=1):
        """
        根据值删除对应行
        :param worksheet: 工作表对象
        :param value: 要查找的值
        :param column: 查找的列（默认第1列）
        :return: 是否成功删除
        """
        try:
            # 在指定列查找值
            cell = worksheet.find(value, in_column=column)
            if cell:
                worksheet.delete_rows(cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False  # 未找到值，无需删除
        except Exception as e:
            raise Exception(f"Failed to delete record: {str(e)}")

    def clear_worksheet(self, worksheet):
        """清空工作表数据（保留表头）"""
        try:
            # 获取表头
            headers = worksheet.row_values(1)
            # 清空所有数据
            worksheet.clear()
            # 重新写入表头
            if headers:
                worksheet.append_row(headers)
        except Exception as e:
            raise Exception(f"Failed to clear worksheet: {str(e)}")
