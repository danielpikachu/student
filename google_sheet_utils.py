import gspread
from google.oauth2.service_account import Credentials
import streamlit as st 
import os

class GoogleSheetHandler:
    """Google Sheets操作工具类，补充缺失的写入方法"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()

    def _authorize(self):
        """认证逻辑：优先使用Streamlit Secrets，兼容本地文件"""
        try:
            if "google_credentials" in st.secrets:
                creds_dict = st.secrets["google_credentials"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
            else:
                raise FileNotFoundError("未找到有效的Google凭证。请检查本地文件路径或Streamlit Secrets配置")
            
            return gspread.authorize(creds)
        
        except Exception as e:
            st.error(f"密钥配置错误：{str(e)}。请检查Streamlit Secrets")
            raise

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """获取指定工作表对象"""
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
        """向工作表追加一行数据"""
        worksheet.append_row(data)

    def delete_record_by_value(self, worksheet, value):
        """根据值删除对应行"""
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

    # 新增：创建/写入工作表方法（解决原错误核心）
    def write_sheet(self, spreadsheet_name, worksheet_name, data):
        """创建工作表并写入数据（若不存在则创建）"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            # 尝试获取工作表，不存在则创建
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows="1000",  # 初始行数
                    cols="20"     # 初始列数
                )
            # 清除现有数据并写入新数据
            worksheet.clear()
            worksheet.append_rows(data)
            return worksheet
        except gspread.SpreadsheetNotFound:
            raise Exception(f"表格不存在: {spreadsheet_name}")
        except Exception as e:
            raise Exception(f"写入工作表失败: {str(e)}")

    # 新增：批量获取工作表数据（用于读取完整表格内容）
    def get_sheet_data(self, spreadsheet_name, worksheet_name):
        """获取工作表所有行数据（列表形式，包含表头）"""
        worksheet = self.get_worksheet(spreadsheet_name, worksheet_name)
        return worksheet.get_all_values()
