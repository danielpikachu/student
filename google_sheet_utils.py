import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os

class GoogleSheetHandler:
    """Google Sheets operation utility class, supplements missing write methods"""
    def __init__(self, credentials_path, scope=None):
        self.credentials_path = credentials_path
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()

    def _authorize(self):
        """Authentication logic: prioritize using Streamlit Secrets, compatible with local files"""
        try:
            if "google_credentials" in st.secrets:
                creds_dict = st.secrets["google_credentials"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=self.scope)
            elif self.credentials_path and os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
            else:
                raise FileNotFoundError("No valid Google credentials found. Please check local file path or Streamlit Secrets configuration")
            
            return gspread.authorize(creds)
        
        except Exception as e:
            st.error(f"Credential configuration error: {str(e)}. Please check Streamlit Secrets")
            raise

    def get_worksheet(self, spreadsheet_name, worksheet_name):
        """Get specified worksheet object"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            return spreadsheet.worksheet(worksheet_name)
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except gspread.WorksheetNotFound:
            raise Exception(f"Worksheet not found: {worksheet_name}")
        except Exception as e:
            raise Exception(f"Failed to get worksheet: {str(e)}")

    def get_all_records(self, worksheet):
        """Get all records from worksheet (list of dictionaries)"""
        return worksheet.get_all_records()

    def append_record(self, worksheet, data):
        """Append a row of data to the worksheet"""
        worksheet.append_row(data)

    def delete_record_by_value(self, worksheet, value):
        """Delete corresponding row based on value"""
        try:
            cell = worksheet.find(value)
            if cell:
                worksheet.delete_rows(cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False
        except Exception as e:
            raise Exception(f"Failed to delete record: {str(e)}")

    # New: Create/write worksheet method (core solution for original error)
    def write_sheet(self, spreadsheet_name, worksheet_name, data):
        """Create worksheet and write data (create if not exists)"""
        try:
            spreadsheet = self.client.open(spreadsheet_name)
            # Try to get worksheet, create if not exists
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows="1000",  # Initial number of rows
                    cols="20"     # Initial number of columns
                )
            # Clear existing data and write new data
            worksheet.clear()
            worksheet.append_rows(data)
            return worksheet
        except gspread.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {spreadsheet_name}")
        except Exception as e:
            raise Exception(f"Failed to write to worksheet: {str(e)}")

    # New: Batch get worksheet data (for reading complete table content)
    def get_sheet_data(self, spreadsheet_name, worksheet_name):
        """Get all row data from worksheet (list format, including header)"""
        worksheet = self.get_worksheet(spreadsheet_name, worksheet_name)
        return worksheet.get_all_values()
