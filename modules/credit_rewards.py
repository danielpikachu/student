# modules/credit_rewards.py
import streamlit as st
import sys
import os
import gspread

# Solve root directory import issue
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Reuse existing Google Sheets utility class
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    st.header("🎓 Credit Information List")
    st.markdown("---")
    st.caption("Data is synced in real-time from Google Sheets (Spreadsheet: Student, Worksheets: credits and information)")

    try:
        # 1. Initialize utility class
        credentials_path = ""
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 2. Configure main spreadsheet name
        spreadsheet_name = "Student"

        # 3. Open main spreadsheet
        try:
            spreadsheet = gsheet.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            st.error(f"❌ Spreadsheet '{spreadsheet_name}' does not exist")
            st.info("Please check if there is a Google Spreadsheet named 'Student'")
            return

        # ---------------------- Read credit data (credits worksheet) ----------------------
        worksheet_credits = "credits"  # Credits data worksheet
        try:
            worksheet_1 = spreadsheet.worksheet(worksheet_credits)
            credit_data = gsheet.get_all_records(worksheet_1)
        except gspread.WorksheetNotFound:
            st.error(f"❌ Worksheet '{worksheet_credits}' does not exist")
            st.info("Please create a worksheet named 'credits' in the 'Student' spreadsheet")
            return

        # Display credit data
        if not credit_data:
            st.info(f"No data available in worksheet '{worksheet_credits}'")
            return

        with st.container(height=450):
            st.dataframe(credit_data, use_container_width=True, hide_index=True)

        # ---------------------- Read information data (information worksheet) ----------------------
        worksheet_info = "information"  # Information worksheet (needs to be created in Google Sheet)
        info_data = None
        try:
            worksheet_2 = spreadsheet.worksheet(worksheet_info)
            info_data = gsheet.get_all_records(worksheet_2)  # Read data from new worksheet
        except gspread.WorksheetNotFound:
            st.warning(f"⚠️ Worksheet '{worksheet_info}' does not exist, will display default information table")
            # If worksheet doesn't exist, display default static data
            info_data = {
                "Reward Content": ["Milk Tea", "Potato Chips", "Coffee Shop Coupon", "Dance Ticket"],
                "Required Credits": [50, 30, 80, 150]
            }

        # ---------------------- Display statistics and information table side by side ----------------------
        col1, col2 = st.columns([0.4, 0.6])

        with col1:
            st.markdown("### Statistical Information")
            st.markdown(f"- Total Records: **{len(credit_data)}**")
            # Additional statistics can be added, for example:
            # total_credits = sum(item.get("Credits", 0) for item in credit_data)
            # st.markdown(f"- Total Credits: **{total_credits}**")

        with col2:
            st.markdown("### Information Table")
            if info_data:
                st.dataframe(info_data, use_container_width=True)
            else:
                st.info("No data in information table")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("Troubleshooting steps:\n1. Confirm spreadsheet and worksheet names are correct\n2. Ensure service account has access permissions")

if __name__ == "__main__":
    render_credit_rewards()
