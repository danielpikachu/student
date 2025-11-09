# modules/money_transfers.py
import streamlit as st
from datetime import datetime
import uuid
import sys
import os
# Resolve root directory module import issue
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# Import Google Sheets utility class
from google_sheet_utils import GoogleSheetHandler

def render_money_transfers():
    """Render money transfer module interface (tra_ namespace)"""
    st.header("💸 Money Transfers")
    st.markdown("---")
    # Initialize Google Sheets connection
    sheet_handler = None
    transfers_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        transfers_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="MoneyTransfers"
        )
    except Exception as e:
        st.error(f"Google Sheets initialization failed: {str(e)}")
    # Sync data from Google Sheets (using tra_records state)
    if transfers_sheet and sheet_handler and (not st.session_state.get("tra_records")):
        try:
            all_data = transfers_sheet.get_all_values()
            expected_headers = ["uuid", "date", "type", "amount", "description", "handler"]
            
            # Check headers
            if not all_data or all_data[0] != expected_headers:
                transfers_sheet.clear()
                transfers_sheet.append_row(expected_headers)
                records = []
            else:
                # Process data (skip header row)
                records = [
                    {
                        "uuid": row[0],
                        "date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "type": row[2],
                        "amount": float(row[3]),
                        "description": row[4],
                        "handler": row[5]
                    } 
                    for row in all_data[1:] 
                    if row[0]  # Ensure UUID is not empty
                ]
            
            st.session_state.tra_records = records
        except Exception as e:
            st.warning(f"Data synchronization failed: {str(e)}")
    # Initialize state (prevent errors on first load)
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []
    # ---------------------- Transaction History Display (with scrollbar, showing 4 records) ----------------------
    st.subheader("Transaction History")
    if not st.session_state.tra_records:
        st.info("No financial transactions recorded yet")
    else:
        # Define column width ratios (ensure last column has enough space for delete button)
        col_widths = [0.3, 1.2, 1.2, 1.2, 2.5, 1.5, 1.0]  # Total remains 8.9
        
        # Display fixed header
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Date**")
        with header_cols[2]:
            st.write("**Amount ($)**")
        with header_cols[3]:
            st.write("**Type**")
        with header_cols[4]:
            st.write("**Description**")
        with header_cols[5]:
            st.write("**Handled By**")
        with header_cols[6]:
            # Only show Action column header for admins
            if st.session_state.auth_is_admin:
                st.write("**Action**")
        
        st.markdown("---")
        
        # Create scrollable container (fixed height, shows 4 records)
        scroll_container = st.container(height=320)  # Each record ~80px, 4 records = 320px
        with scroll_container:
            # Iterate through and display each transaction
            for idx, trans in enumerate(st.session_state.tra_records, 1):
                unique_key = f"tra_delete_{idx}_{trans['uuid']}"
                cols = st.columns(col_widths)
                
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(trans["date"].strftime("%Y-%m-%d"))
                with cols[2]:
                    st.write(f"${trans['amount']:.2f}")
                with cols[3]:
                    st.write(trans["type"])
                with cols[4]:
                    st.write(trans["description"])
                with cols[5]:
                    st.write(trans["handler"])
                with cols[6]:
                    # Only admins can see delete button
                    if st.session_state.auth_is_admin:
                        if st.button(
                            "🗑️ Delete", 
                            key=unique_key,
                            use_container_width=True,
                            type="secondary"
                        ):
                            # Delete from local state
                            st.session_state.tra_records.pop(idx - 1)
                            
                            # Sync deletion to Google Sheets
                            if transfers_sheet and sheet_handler:
                                try:
                                    cell = transfers_sheet.find(trans["uuid"])
                                    if cell:
                                        transfers_sheet.delete_rows(cell.row)
                                    st.success(f"Transaction {idx} deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.warning(f"Synchronization of deletion failed: {str(e)}")
                
                # Row separator
                st.markdown("---")
        
        # Display summary information
        total_income = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Income")
        total_expense = sum(t["amount"] for t in st.session_state.tra_records if t["type"] == "Expense")
        net_balance = total_income - total_expense
        
        st.markdown(f"""
        <div style='margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;'>
            <strong>Summary:</strong><br>
            Total Income: ${total_income:.2f} | 
            Total Expense: ${total_expense:.2f} | 
            Net Balance: ${net_balance:.2f}
        </div>
        """, unsafe_allow_html=True)
    st.write("=" * 50)
    # ---------------------- Add New Transaction (Admin only) ----------------------
    if st.session_state.auth_is_admin:
        st.subheader("Record New Transaction")
        col1, col2 = st.columns(2)
        
        with col1:
            trans_date = st.date_input(
                "Transaction Date", 
                value=datetime.today(),
                key="tra_input_date"
            )
            
            amount = st.number_input(
                "Amount ($)", 
                min_value=0.01, 
                step=10.00, 
                value=100.00,
                key="tra_input_amount"
            )
            
            trans_type = st.radio(
                "Transaction Type", 
                ["Income", "Expense"], 
                index=0,
                key="tra_radio_type"
            )
        
        with col2:
            description = st.text_input(
                "Description", 
                value="Fundraiser proceeds",
                key="tra_input_desc"
            ).strip()
            
            handler = st.text_input(
                "Handled By", 
                value="",
                key="tra_input_handler"
            ).strip()
        # Record transaction button
        if st.button("Record Transaction", key="tra_btn_record", use_container_width=True, type="primary"):
            # Validate required fields
            if not description or not handler:
                st.error("Description and Handled By are required fields!")
                return
            
            # Create new transaction record
            new_trans = {
                "uuid": str(uuid.uuid4()),  # Generate unique identifier
                "date": trans_date,
                "type": trans_type,
                "amount": round(amount, 2),
                "description": description,
                "handler": handler
            }
            
            # Update local state
            st.session_state.tra_records.append(new_trans)
            
            # Sync to Google Sheets
            if transfers_sheet and sheet_handler:
                try:
                    transfers_sheet.append_row([
                        new_trans["uuid"],
                        new_trans["date"].strftime("%Y-%m-%d"),
                        new_trans["type"],
                        str(new_trans["amount"]),
                        new_trans["description"],
                        new_trans["handler"]
                    ])
                    st.success("Transaction recorded successfully!")
                    st.rerun()
                except Exception as e:
                    st.warning(f"Synchronization to Google Sheets failed: {str(e)}")
    else:
        # Display message for non-admins
        st.info("You do not have editing permissions. You can only view transaction records.")
