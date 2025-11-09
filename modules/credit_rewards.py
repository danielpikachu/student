# modules/credit_rewards.py
import streamlit as st
import sys
import os
import gspread

# Fix root directory import issue
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Reuse existing Google Sheets utility class
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    st.header("🎓 Credit Information List")
    st.markdown("---")
    st.caption("Data is synced in real-time from Google Sheets (Spreadsheet: Student, Worksheet: credits)")

    try:
        # 1. Initialize the utility class
        credentials_path = ""
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 2. Configure spreadsheet and worksheet information
        spreadsheet_name = "Student"
        worksheet_name = "credits"

        # 3. Verify spreadsheet exists (without success message)
        try:
            spreadsheet = gsheet.client.open(spreadsheet_name)
            # 已删除成功提示行
        except gspread.SpreadsheetNotFound:
            st.error(f"❌ Spreadsheet '{spreadsheet_name}' not found")
            st.info("Please check if the Google Sheet named 'Student' exists and hasn't been renamed")
            return

        # 4. Verify worksheet exists (without success message)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            # 已删除成功提示行
        except gspread.WorksheetNotFound:
            st.error(f"❌ Worksheet '{worksheet_name}' not found in spreadsheet '{spreadsheet_name}'")
            st.info("Please check if a worksheet named 'credits' exists in your 'Student' spreadsheet (case-sensitive)")
            return

        # 5. Read and display data
        credit_data = gsheet.get_all_records(worksheet)

        if not credit_data:
            st.info(f"No data found in worksheet '{worksheet_name}'. Please add data in Google Sheets and try again.")
            return

        with st.container(height=450):
            st.dataframe(credit_data, use_container_width=True, hide_index=True)

        st.markdown("### Statistics")
        st.markdown(f"- Total records: **{len(credit_data)}**")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Troubleshooting steps:\n1. Verify spreadsheet name is 'Student' (case-sensitive)\n2. Verify worksheet name is 'credits' (case-sensitive)\n3. Ensure service account has access to the spreadsheet")

if __name__ == "__main__":
    render_credit_rewards()
