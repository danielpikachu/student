import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import time
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError  # 新增：处理API错误

class GoogleSheetHandler:
    """Google Sheets operation utility class with quota optimization"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()
        # 新增：缓存机制（默认5分钟有效期）
        self.cache = {}  # 格式: {(spreadsheet_name, worksheet_name): (data, expire_time)}
        self.cache_ttl = timedelta(minutes=5)

    def _authorize(self):
        """Authentication logic: prioritize using Streamlit Secrets"""
        try:
            if "google_credentials" in st.secrets:
                creds_dict = st.secrets["google_credentials"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
            else:
                raise FileNotFoundError("No valid Google credentials found")
            
            return gspread.authorize(creds)
        
        except Exception as e:
            st.error(f"Credential error: {str(e)}")
            raise

    # 新增：请求重试装饰器（核心优化）
    def _retry_with_backoff(self, func, *args, **kwargs):
        """带指数退避的重试机制，处理429配额超额错误"""
        max_retries = 3
        retry_delay = 5  # 初始延迟5秒
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status == 429:  # 配额超限
                    if attempt < max_retries - 1:
                        st.warning(f"请求频繁，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避（5→10→20秒）
                        continue
                    else:
                        raise Exception(f"超过最大重试次数：{str(e)}")
                else:
                    raise  # 其他HTTP错误直接抛出
            except gspread.exceptions.APIError as e:
                # 兼容gspread封装的API错误
                if "429" in str(e):
                    if attempt < max_retries - 1:
                        st.warning(f"请求频繁，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise Exception(f"超过最大重试次数：{str(e)}")
                else:
                    raise
            except Exception as e:
                raise  # 非API错误直接抛出

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """获取指定工作表（添加重试）"""
        try:
            # 用重试机制包装核心调用
            spreadsheet = self._retry_with_backoff(self.client.open, spreadsheet_name)
            return self._retry_with_backoff(spreadsheet.worksheet, worksheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except gspread.WorksheetNotFound:
            raise Exception(f"Worksheet not found: {worksheet_name}")
        except Exception as e:
            raise Exception(f"Failed to get worksheet: {str(e)}")

    def get_all_records(self, worksheet):
        """获取所有记录（添加重试）"""
        return self._retry_with_backoff(worksheet.get_all_records)

    def append_record(self, worksheet, data):
        """追加单行数据（添加重试）"""
        self._retry_with_backoff(worksheet.append_row, data)

    # 新增：批量追加多行（供未来模块优化使用，当前模块无需改动）
    def append_records(self, worksheet, data_list):
        """批量追加多行数据"""
        if not data_list:
            return
        self._retry_with_backoff(worksheet.append_rows, data_list)

    def delete_record_by_value(self, worksheet, value):
        """根据值删除行（添加重试）"""
        try:
            cell = self._retry_with_backoff(worksheet.find, value)
            if cell:
                self._retry_with_backoff(worksheet.delete_rows, cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False
        except Exception as e:
            raise Exception(f"Failed to delete record: {str(e)}")

    def write_sheet(self, spreadsheet_name, worksheet_name, data):
        """创建/写入工作表（添加重试）"""
        try:
            spreadsheet = self._retry_with_backoff(self.client.open, spreadsheet_name)
            try:
                worksheet = self._retry_with_backoff(spreadsheet.worksheet, worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = self._retry_with_backoff(
                    spreadsheet.add_worksheet,
                    title=worksheet_name,
                    rows="1000",
                    cols="20"
                )
            self._retry_with_backoff(worksheet.clear)
            self._retry_with_backoff(worksheet.append_rows, data)
            return worksheet
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except Exception as e:
            raise Exception(f"Failed to write to worksheet: {str(e)}")

    def get_sheet_data(self, spreadsheet_name, worksheet_name):
        """获取工作表数据（添加缓存和重试）"""
        cache_key = (spreadsheet_name, worksheet_name)
        now = datetime.now()
        
        # 检查缓存是否有效
        if cache_key in self.cache:
            cached_data, expire_time = self.cache[cache_key]
            if now < expire_time:
                return cached_data
        
        # 缓存无效时重新获取
        worksheet = self.get_worksheet(spreadsheet_name, worksheet_name)
        data = self._retry_with_backoff(worksheet.get_all_values)
        # 更新缓存
        self.cache[cache_key] = (data, now + self.cache_ttl)
        return data

    # 新增：手动清除缓存（可选，供特殊场景使用）
    def clear_cache(self, spreadsheet_name=None, worksheet_name=None):
        if spreadsheet_name and worksheet_name:
            key = (spreadsheet_name, worksheet_name)
            if key in self.cache:
                del self.cache[key]
        else:
            self.cache = {}
