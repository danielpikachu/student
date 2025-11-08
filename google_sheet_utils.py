import gspread
from google.oauth2.service_account import Credentials
import streamlit as st 
import os  # 新增：处理路径验证

class GoogleSheetHandler:
    """恢复原兼容逻辑：确保返回gspread客户端对象"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()  # 关键：生成gspread客户端

    def _authorize(self):
        """恢复原认证逻辑，确保返回gspread.authorize后的客户端"""
        try:
            # 1. 优先从Streamlit Secrets读取（原逻辑）
            if "google_credentials" in st.secrets:
                creds_dict = st.secrets["google_credentials"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            # 2. 兼容本地凭证文件（原逻辑，处理空路径）
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
            else:
                # 当既无本地凭证文件也无secrets配置时，明确抛出错误
                raise FileNotFoundError("未找到有效的Google凭证。请检查本地文件路径或Streamlit Secrets配置")
            
            # 核心修复：返回gspread客户端（原代码可能漏掉这步）
            return gspread.authorize(creds)
        
        except Exception as e:
            st.error(f"密钥配置错误：{str(e)}。请检查Streamlit Secrets")
            raise

    # 以下方法完全保留原逻辑，不做任何修改
    def get_worksheet(self, spreadsheet_name, worksheet_name):
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            return spreadsheet.worksheet(worksheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"表格不存在: {spreadsheet_name}")
        except gspread.WorksheetNotFound:
            raise Exception(f"工作表不存在: {worksheet_name}")
        except Exception as e:
            raise Exception(f"获取工作表失败: {str(e)}")

    def get_all_records(self, worksheet):
        return worksheet.get_all_records()

    def append_record(self, worksheet, data):
        worksheet.append_row(data)

    def delete_record_by_value(self, worksheet, value):
        try:
            cell = worksheet.find(value)
            if cell:
                worksheet.delete_rows(cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False
        except Exception as e:
            raise Exception(f"删除记录失败: {str(e)}")
