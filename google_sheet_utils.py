import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import time
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError  # New: Handle API errors

class GoogleSheetHandler:
    """Google Sheets operation utility class with quota optimization"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()
        # New: Caching mechanism (5-minute default validity)
        self.cache = {}  # Format: {(spreadsheet_name, worksheet_name): (data, expire_time)}
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

    # New: Request retry decorator (core optimization)
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry mechanism with exponential backoff for handling 429 quota exceeded errors"""
        max_retries = 3
        retry_delay = 5  # Initial delay of 5 seconds
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if e.resp.status == 429:  # Quota exceeded
                    if attempt < max_retries - 1:
                        st.warning(f"Requests too frequent, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff (5→10→20 seconds)
                        continue
                    else:
                        raise Exception(f"Exceeded maximum retry attempts: {str(e)}")
                else:
                    raise  # Directly raise other HTTP errors
            except gspread.exceptions.APIError as e:
                # Compatible with gspread-wrapped API errors
                if "429" in str(e):
                    if attempt < max_retries - 1:
                        st.warning(f"Requests too frequent, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise Exception(f"Exceeded maximum retry attempts: {str(e)}")
                else:
                    raise
            except Exception as e:
                raise  # Directly raise non-API errors

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """Get specified worksheet (with retry)"""
        try:
            # Wrap core calls with retry mechanism
            spreadsheet = self._retry_with_backoff(self.client.open, spreadsheet_name)
            return self._retry_with_backoff(spreadsheet.worksheet, worksheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except gspread.WorksheetNotFound:
            raise Exception(f"Worksheet not found: {worksheet_name}")
        except Exception as e:
            raise Exception(f"Failed to get worksheet: {str(e)}")

    def get_all_records(self, worksheet):
        """Get all records (with retry)"""
        return self._retry_with_backoff(worksheet.get_all_records)

    def append_record(self, worksheet, data):
        """Append single row of data (with retry)"""
        self._retry_with_backoff(worksheet.append_row, data)

    # New: Batch append multiple rows (for future module optimization, no changes needed in current module)
    def append_records(self, worksheet, data_list):
        """Batch append multiple rows of data"""
        if not data_list:
            return
        self._retry_with_backoff(worksheet.append_rows, data_list)

    def delete_record_by_value(self, worksheet, value):
        """Delete row by value (with retry)"""
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
        """Create/write to worksheet (with retry)"""
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
        """Get worksheet data (with caching and retry)"""
        cache_key = (spreadsheet_name, worksheet_name)
        now = datetime.now()
        
        # Check if cache is valid
        if cache_key in self.cache:
            cached_data, expire_time = self.cache[cache_key]
            if now < expire_time:
                return cached_data
        
        # Fetch new data when cache is invalid
        worksheet = self.get_worksheet(spreadsheet_name, worksheet_name)
        data = self._retry_with_backoff(worksheet.get_all_values)
        # Update cache
        self.cache[cache_key] = (data, now + self.cache_ttl)
        return data

    # New: Manually clear cache (optional, for special scenarios)
    def clear_cache(self, spreadsheet_name=None, worksheet_name=None):
        if spreadsheet_name and worksheet_name:
            key = (spreadsheet_name, worksheet_name)
            if key in self.cache:
                del self.cache[key]
        else:
            self.cache = {}
