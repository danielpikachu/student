# modules/groups.py
import streamlit as st
import pandas as pd
import uuid
import sys
import os
from datetime import datetime

# Solve root directory module import issue
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# Define allowed access codes and corresponding group names (8 groups)
ACCESS_CODES = {
    "GROUP001": "Group 1",
    "GROUP002": "Group 2",
    "GROUP003": "Group 3",
    "GROUP004": "Group 4",
    "GROUP005": "Group 5",
    "GROUP006": "Group 6",
    "GROUP007": "Group 7",
    "GROUP008": "Group 8"
}

def render_groups():
    st.set_page_config(page_title="Student Affairs Management", layout="wide")
    
    # Initialize session state (record login status, current group information)
    if "group_logged_in" not in st.session_state:
        st.session_state.group_logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:  # Store current group's access code (e.g., GROUP001)
        st.session_state.current_group_code = None
    # Initialize data storage (members, incomes, expenses)
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # Login interface
    if not st.session_state.group_logged_in:
        st.markdown("<h2>📋 Student Affairs Management System</h2>", unsafe_allow_html=True)
        st.caption("Please enter the access code to enter the corresponding group management")
        st.divider()
        
        access_code = st.text_input("Access Code", placeholder="e.g., GROUP001", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                if access_code in ACCESS_CODES:
                    st.session_state.group_logged_in = True
                    st.session_state.current_group = ACCESS_CODES[access_code]
                    st.session_state.current_group_code = access_code
                    st.success(f"Login successful, welcome to {ACCESS_CODES[access_code]}")
                    st.rerun()
                else:
                    st.error("Invalid access code, please try again")
        with col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.group_logged_in = False
                st.session_state.current_group = None
                st.session_state.current_group_code = None
                st.rerun()
        return

    # Logged in state - display group name
    st.markdown(f"<h2>📋 Student Affairs Management System - {st.session_state.current_group}</h2>", unsafe_allow_html=True)
    st.caption("Includes three functional modules: member management, income management, and reimbursement management")
    st.divider()

    # Logout/Switch group button
    if st.button("Switch Group", key="logout_btn"):
        st.session_state.group_logged_in = False
        st.session_state.current_group = None
        st.session_state.current_group_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.session_state.expenses = []
        st.rerun()

    # Initialize Google Sheets connection (single sheet AllGroupsData)
    sheet_handler = None
    main_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")  # Ensure credentials are configured correctly
        # Connect to the AllGroupsData worksheet in the existing Group file
        main_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",  # Your Google Sheet file name
            worksheet_name="AllGroupsData"  # Worksheet name
        )
    except Exception as e:
        st.error(f"Google Sheets initialization failed: {str(e)}")
        # If worksheet doesn't exist, try to create it automatically (ensure permission)
        if "Worksheet not found" in str(e) and sheet_handler:
            with st.spinner("Trying to create worksheet AllGroupsData..."):
                try:
                    main_sheet = sheet_handler.create_worksheet(
                        spreadsheet_name="Student",
                        worksheet_name="AllGroupsData",
                        rows=1000,
                        cols=20
                    )
                    # Initialize header row
                    headers = ["group_code", "data_type", "uuid", 
                               "name", "student_id",  # Member-specific fields
                               "date", "amount", "description",  # Income/reimbursement specific fields
                               "created_at"]  # Data creation time
                    main_sheet.append_row(headers)
                    st.success("Worksheet AllGroupsData created successfully!")
                except Exception as e2:
                    st.error(f"Failed to create worksheet: {str(e2)}")

    # Sync current group's data from single sheet (members, incomes, reimbursements)
    current_code = st.session_state.current_group_code
    if main_sheet and sheet_handler:
        try:
            all_rows = main_sheet.get_all_values()
            if len(all_rows) < 1:
                st.warning("Worksheet is empty, initializing header...")
                headers = ["group_code", "data_type", "uuid", "name", "student_id", 
                           "date", "amount", "description", "created_at"]
                main_sheet.append_row(headers)
                all_rows = [headers]
            
            # Parse header row to determine field indices (avoid errors from field order changes)
            header = all_rows[0]
            col_indices = {col: idx for idx, col in enumerate(header)}
            required_cols = ["group_code", "data_type", "uuid", "created_at"]
            if not all(col in col_indices for col in required_cols):
                st.error("Worksheet header format is incorrect, please check if fields are complete")
                return

            # Filter current group's member data (data_type=member)
            st.session_state.members = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "name": row[col_indices["name"]],
                    "student_id": row[col_indices["student_id"]]
                }
                for row in all_rows[1:]  # Skip header row
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "member"
            ]

            # Filter current group's income data (data_type=income)
            st.session_state.incomes = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]]
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "income"
            ]

            # Filter current group's reimbursement data (data_type=expense)
            st.session_state.expenses = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]]
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "expense"
            ]

        except Exception as e:
            st.warning(f"Data synchronization failed: {str(e)}")

    # Create horizontal tabs
    tab1, tab2, tab3 = st.tabs(["👥 Member Management", "💰 Income Management", "🧾 Reimbursement Management"])

    # ---------------------- Member Management Module (Tab 1) ----------------------
    with tab1:
        st.markdown("<h3 style='font-size: 16px'>Member Management</h3>", unsafe_allow_html=True)
        st.write("Manage basic information of members (name, student ID)")
        st.divider()

        # Add new member
        with st.container():
            st.markdown("**Add New Member**", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Member Name*", placeholder="Please enter name")
            with col2:
                student_id = st.text_input("Student ID*", placeholder="Please enter unique ID")
            
            if st.button("Confirm Add Member", use_container_width=True, key="add_member"):
                if not name or not student_id:
                    st.error("Name and Student ID cannot be empty")
                    return
                if any(m["student_id"] == student_id for m in st.session_state.members):
                    st.error(f"Student ID {student_id} already exists")
                    return

                # Generate unique ID
                member_uuid = str(uuid.uuid4())
                new_member = {
                    "uuid": member_uuid,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                }
                st.session_state.members.append(new_member)

                # Write to Google Sheet (single sheet)
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,  # group_code
                            "member",      # data_type
                            member_uuid,   # uuid
                            name.strip(),  # name
                            student_id.strip(),  # student_id
                            "", "", "",    # Leave income/reimbursement fields empty
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # created_at
                        ])
                        st.success(f"Successfully added member: {name}")
                    except Exception as e:
                        st.warning(f"Failed to sync to sheet: {str(e)}")

        # Display member list
        st.divider()
        st.markdown("**Member List**", unsafe_allow_html=True)
        if not st.session_state.members:
            st.info("No members yet, please add")
        else:
            member_df = pd.DataFrame([
                {"Serial No.": i+1, "Name": m["name"], "Student ID": m["student_id"]}
                for i, m in enumerate(st.session_state.members)
            ])
            st.dataframe(member_df, use_container_width=True)

            # Delete member
            with st.expander("Delete Member", expanded=False):
                for m in st.session_state.members:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{m['name']} (ID: {m['student_id']})")
                    with col2:
                        if st.button("Delete", key=f"del_member_{m['uuid']}"):
                            # Local deletion
                            st.session_state.members = [x for x in st.session_state.members if x["uuid"] != m["uuid"]]
                            # Sheet deletion (locate by uuid)
                            if main_sheet:
                                try:
                                    cell = main_sheet.find(m["uuid"])
                                    if cell:
                                        row = main_sheet.row_values(cell.row)
                                        # Double verification: ensure it's current group's data
                                        if row[0] == current_code and row[1] == "member":
                                            main_sheet.delete_rows(cell.row)
                                            st.success(f"Deleted {m['name']}")
                                            st.rerun()
                                except Exception as e:
                                    st.warning(f"Deletion sync failed: {str(e)}")

    # ---------------------- Income Management Module (Tab 2) ----------------------
    with tab2:
        st.markdown("<h3 style='font-size: 16px'>Income Management</h3>", unsafe_allow_html=True)
        st.write("Record and manage various income information")
        st.divider()

        # Add new income
        with st.container():
            st.markdown("**Add New Income**", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                income_date = st.date_input("Date*", datetime.now())
            with col2:
                income_amount = st.number_input("Amount*", min_value=0.01, step=0.01, format="%.2f")
            with col3:
                income_desc = st.text_input("Description*", placeholder="Please enter income source")
            
            if st.button("Confirm Add Income", use_container_width=True, key="add_income"):
                if not income_desc:
                    st.error("Income description cannot be empty")
                    return

                income_uuid = str(uuid.uuid4())
                new_income = {
                    "uuid": income_uuid,
                    "date": income_date.strftime("%Y-%m-%d"),
                    "amount": f"{income_amount:.2f}",
                    "description": income_desc.strip()
                }
                st.session_state.incomes.append(new_income)

                # Write to Google Sheet
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,
                            "income",
                            income_uuid,
                            "", "",  # Leave member fields empty
                            new_income["date"],
                            new_income["amount"],
                            new_income["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        st.success(f"Successfully added income: ¥{income_amount:.2f}")
                    except Exception as e:
                        st.warning(f"Failed to sync to sheet: {str(e)}")

        # Display income list
        st.divider()
        st.markdown("**Income List**", unsafe_allow_html=True)
        if not st.session_state.incomes:
            st.info("No income records yet, please add")
        else:
            income_df = pd.DataFrame([
                {"Serial No.": i+1, "Date": m["date"], "Amount (¥)": m["amount"], "Description": m["description"]}
                for i, m in enumerate(st.session_state.incomes)
            ])
            st.dataframe(income_df, use_container_width=True)

            # Delete income
            with st.expander("Delete Income", expanded=False):
                for income in st.session_state.incomes:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{income['date']} - ¥{income['amount']}: {income['description']}")
                    with col2:
                        if st.button("Delete", key=f"del_income_{income['uuid']}"):
                            st.session_state.incomes = [x for x in st.session_state.incomes if x["uuid"] != income["uuid"]]
                            if main_sheet:
                                try:
                                    cell = main_sheet.find(income["uuid"])
                                    if cell:
                                        row = main_sheet.row_values(cell.row)
                                        if row[0] == current_code and row[1] == "income":
                                            main_sheet.delete_rows(cell.row)
                                            st.success("Income record deleted")
                                            st.rerun()
                                except Exception as e:
                                    st.warning(f"Deletion sync failed: {str(e)}")

    # ---------------------- Reimbursement Management Module (Tab 3) ----------------------
    with tab3:
        st.markdown("<h3 style='font-size: 16px'>Reimbursement Management</h3>", unsafe_allow_html=True)
        st.write("Record and manage various reimbursement information")
        st.divider()

        # Add new reimbursement
        with st.container():
            st.markdown("**Add New Reimbursement**", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                exp_date = st.date_input("Reimbursement Date*", datetime.now(), key="exp_date")
            with col2:
                exp_amount = st.number_input("Reimbursement Amount*", min_value=0.01, step=0.01, format="%.2f", key="exp_amount")
            with col3:
                exp_desc = st.text_input("Reimbursement Description*", placeholder="Please enter reimbursement reason", key="exp_desc")
            
            if st.button("Confirm Add Reimbursement", use_container_width=True, key="add_expense"):
                if not exp_desc:
                    st.error("Reimbursement description cannot be empty")
                    return

                exp_uuid = str(uuid.uuid4())
                new_exp = {
                    "uuid": exp_uuid,
                    "date": exp_date.strftime("%Y-%m-%d"),
                    "amount": f"{exp_amount:.2f}",
                    "description": exp_desc.strip()
                }
                st.session_state.expenses.append(new_exp)

                # Write to Google Sheet
                if main_sheet:
                    try:
                        main_sheet.append_row([
                            current_code,
                            "expense",  # data type is expense
                            exp_uuid,
                            "", "",  # Leave member fields empty
                            new_exp["date"],
                            new_exp["amount"],
                            new_exp["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        st.success(f"Successfully added reimbursement: ¥{exp_amount:.2f}")
                    except Exception as e:
                        st.warning(f"Failed to sync to sheet: {str(e)}")

        # Display reimbursement list
        st.divider()
        st.markdown("**Reimbursement List**", unsafe_allow_html=True)
        if not st.session_state.expenses:
            st.info("No reimbursement records yet, please add")
        else:
            exp_df = pd.DataFrame([
                {"Serial No.": i+1, "Date": m["date"], "Amount (¥)": m["amount"], "Description": m["description"]}
                for i, m in enumerate(st.session_state.expenses)
            ])
            st.dataframe(exp_df, use_container_width=True)

            # Add reimbursement deletion function (same logic as income deletion)
            with st.expander("Delete Reimbursement", expanded=False):
                for exp in st.session_state.expenses:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{exp['date']} - ¥{exp['amount']}: {exp['description']}")
                    with col2:
                        if st.button("Delete", key=f"del_expense_{exp['uuid']}"):
                            st.session_state.expenses = [x for x in st.session_state.expenses if x["uuid"] != exp["uuid"]]
                            if main_sheet:
                                try:
                                    cell = main_sheet.find(exp["uuid"])
                                    if cell:
                                        row = main_sheet.row_values(cell.row)
                                        if row[0] == current_code and row[1] == "expense":
                                            main_sheet.delete_rows(cell.row)
                                            st.success("Reimbursement record deleted")
                                            st.rerun()
                                except Exception as e:
                                    st.warning(f"Deletion sync failed: {str(e)}")

    st.divider()
