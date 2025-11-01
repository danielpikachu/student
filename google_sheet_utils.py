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
        """仅从Streamlit Secrets读取凭证（完全云端运行）"""
        try:
            # 直接从Streamlit Secrets获取配置
            creds_dict = st.secrets["google_credentials"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
                
            return gspread.authorize(creds)
        
        except Exception as e:
            st.error(f"密钥配置错误：{str(e)}。请检查Streamlit Secrets")
            raise

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """获取指定表格中的指定工作表"""
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
        """获取工作表所有记录（字典列表）"""
        return worksheet.get_all_records()

    def append_record(self, worksheet, data):
        """向工作表追加一行记录"""
        worksheet.append_row(data)

    def delete_record_by_value(self, worksheet, value):
        """根据值删除对应行（用于删除事件）"""
        try:
            cell = worksheet.find(value)
            if cell:
                worksheet.delete_rows(cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False  # 未找到值，无需删除
        except Exception as e:
            raise Exception(f"删除记录失败: {str(e)}")
