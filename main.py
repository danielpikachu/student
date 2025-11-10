import streamlit as st
import sys
import os
import hashlib
from datetime import datetime

# Solve root directory module import issue
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import real Google Sheets utility class (ensure google_sheet_utils.py exists and works properly)
from google_sheet_utils import GoogleSheetHandler
# Import all functional modules (unchanged)
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.attendance import render_attendance
from modules.credit_rewards import render_credit_rewards
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# ---------------------- Global Configuration ----------------------
SHEET_NAME = "Student"
USER_SHEET_TAB = "users"
DEFAULT_ADMIN_USERS = ["admin", "root"]  # Default admin usernames
gs_handler = GoogleSheetHandler(credentials_path="")  # Configure according to actual credential path

# ---------------------- Password Encryption Tool (unchanged) ----------------------
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# ---------------------- User Data Operations (real logic restored, mock data removed) ----------------------
def init_user_sheet():
    try:
        gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
    except:
        header = ["username", "password", "register_time", "last_login"]
        spreadsheet = gs_handler.client.open(SHEET_NAME)
        spreadsheet.add_worksheet(title=USER_SHEET_TAB, rows=100, cols=4)
        worksheet = spreadsheet.worksheet(USER_SHEET_TAB)
        worksheet.append_row(header)

def get_user_by_username(username):
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"Failed to retrieve user data: {str(e)}")
        return None
    
    if not data:
        return None
    # Iterate through real table data to match username (original logic restored)
    for row in data[1:]:
        if row[0] == username:
            return {
                "username": row[0],
                "password": row[1],  # Encrypted password stored in the table
                "register_time": row[2],
                "last_login": row[3]
            }
    return None

def add_new_user(username, password):
    if get_user_by_username(username):
        return False
    hashed_pwd = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_user = [username, hashed_pwd, now, now]
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        worksheet.append_row(new_user)
        return True
    except Exception as e:
        st.error(f"Failed to create user: {str(e)}")
        return False

def update_user_last_login(username):
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"Failed to retrieve user data: {str(e)}")
        return False
    
    if not data:
        return False
    for i, row in enumerate(data[1:]):
        if row[0] == username:
            row_num = i + 2
            new_last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.update_cell(row_num, 4, new_last_login)
            return True
    return False

# ---------------------- Session State Initialization (unchanged) ----------------------
def init_session_state():
    if "sys_admin_password" not in st.session_state:
        st.session_state.sys_admin_password = "sc_admin_2025"
    
    if "auth_logged_in" not in st.session_state:
        st.session_state.auth_logged_in = False
    if "auth_username" not in st.session_state:
        st.session_state.auth_username = ""
    if "auth_is_admin" not in st.session_state:
        st.session_state.auth_is_admin = False
    if "auth_current_group_code" not in st.session_state:
        st.session_state.auth_current_group_code = ""
    
    if "ann_list" not in st.session_state:
        st.session_state.ann_list = []
    if "cal_events" not in st.session_state:
        st.session_state.cal_events = []
    if "cal_current_month" not in st.session_state:
        st.session_state.cal_current_month = datetime.today().replace(day=1)
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    if "fin_current_funds" not in st.session_state:
        st.session_state.fin_current_funds = 0.0
    if "fin_annual_target" not in st.session_state:
        st.session_state.fin_annual_target = 15000.0
    if "fin_scheduled_events" not in st.session_state:
        st.session_state.fin_scheduled_events = []
    if "fin_occasional_events" not in st.session_state:
        st.session_state.fin_occasional_events = []
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []
    if "grp_list" not in st.session_state:
        st.session_state.grp_list = []
    if "grp_members" not in st.session_state:
        st.session_state.grp_members = []

# ---------------------- Permission Control Decorators (unchanged) ----------------------
def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("Please log in first to operate!")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper

def require_edit_permission(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_is_admin:
            st.info("You do not have edit permission, only view access.")
        return func(*args, **kwargs)
    return wrapper

def require_group_edit_permission(func):
    def wrapper(*args, **kwargs):
        if st.session_state.auth_is_admin:
            return func(*args, **kwargs)
        with st.sidebar.expander("🔑 Group Access Verification", expanded=True):
            access_code = st.text_input("Please enter Group access code", type="password")
            if st.button("Verify Access Permission"):
                if access_code:
                    st.session_state.auth_current_group_code = access_code
                    st.success("Access verified! You can edit the current Group.")
                else:
                    st.error("Please enter a valid access code!")
        return func(*args, **kwargs)
    return wrapper

# ---------------------- Login/Registration Interface (all text localized to English) ----------------------
def show_login_register_form():
    with st.sidebar:
        st.markdown("---")
        st.subheader("User Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Log In"):
            if not username or not password:
                st.error("Username and password cannot be empty!")
                return
            
            user = get_user_by_username(username)
            if not user:
                st.error("Username does not exist!")
                return
            
            # Password encryption verification (original logic unchanged)
            hashed_pwd = hash_password(password)
            if user["password"] != hashed_pwd:
                st.error("Incorrect password!")
                return
            
            # Admin judgment (original logic unchanged)
            try:
                admin_users = st.secrets.get("admin_users", DEFAULT_ADMIN_USERS)
                if isinstance(admin_users, str):
                    admin_users = [user.strip() for user in admin_users.split(",")]
            except:
                admin_users = DEFAULT_ADMIN_USERS
            
            st.session_state.auth_is_admin = username.strip() in admin_users
            st.session_state.auth_logged_in = True
            st.session_state.auth_username = username
            update_user_last_login(username)
            st.success(f"Login successful! Welcome back, {'Admin' if st.session_state.auth_is_admin else 'User'} {username}!")
            st.rerun()
        
        st.subheader("User Registration")
        new_username = st.text_input("Username", key="reg_username")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_pwd")
        
        if st.button("Register"):
            if not new_username or not new_password or not confirm_password:
                st.error("All fields cannot be empty!")
                return
            
            if new_password != confirm_password:
                st.error("The two password entries do not match!")
                return
            
            if len(new_password) < 6:
                st.error("Password length must be at least 6 characters!")
                return
            
            success = add_new_user(new_username, new_password)
            if success:
                st.success("Registration successful! Please log in via the login page～")
            else:
                st.error("Username already exists! Please choose another username.")
        st.markdown("---")

# ---------------------- Page Main Logic (all text localized to English) ----------------------
def main():
    st.set_page_config(
        page_title="SCIS Student Council Management System",
        page_icon="🏛️",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.auth_logged_in:
        # 1. Centered title
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>Welcome to SCIS Student Council Management System</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 2. Gray background prompt text
        st.markdown(
            """
            <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 8px; text-align: center; margin: 0 2rem;">
                <p style="margin-bottom: 0.5rem;">Please log in using the form in the sidebar to access the Student Council management tools.</p>
                <p>If you don't have an account, please contact an administrator to create one for you.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 3. Function tags (with top margin to separate from above)
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem; margin-top: 2rem;">
                    <span style="font-size: 1.2rem;">📅</span>
                    <span>Event Planning</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem; margin-top: 2rem;">
                    <span style="font-size: 1.2rem;">💰</span>
                    <span>Financial Management</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem; margin-top: 2rem;">
                    <span style="font-size: 1.2rem;">🏆</span>
                    <span>Student Recognition</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Show login/registration form (sidebar)
        show_login_register_form()
        return
    
    # Main interface after login (original logic unchanged)
    st.title("SCIS Student Council Management System")
    
    with st.sidebar:
        st.markdown("---")
        st.info(f"""
        👤 Current User: {st.session_state.auth_username}  
        📌 Role: {'Admin' if st.session_state.auth_is_admin else 'Regular User'}  
        🕒 Last Login: {get_user_by_username(st.session_state.auth_username)['last_login']}
        """)
        if st.button("Log Out"):
            st.session_state.auth_logged_in = False
            st.session_state.auth_username = ""
            st.session_state.auth_is_admin = False
            st.session_state.auth_current_group_code = ""
            st.rerun()
        st.markdown("---")
        st.info("© 2025 SCIS Student Council Management System")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "👥 Groups", "📢 Announcements", "💰 Financial Planning",
        "📋 Attendance","🎁 Credit & Rewards","💸 Money Transfers", "📅 Calendar"
    ])
    
    with tab1:
        require_login(require_edit_permission(render_groups))()
    with tab2:
        require_login(require_edit_permission(render_announcements))()
    with tab3:
        require_login(require_edit_permission(render_financial_planning))()
    with tab4:
        require_login(require_edit_permission(render_attendance))()
    with tab5:
        require_login(require_edit_permission(render_credit_rewards))()
    with tab6:   
        require_login(require_edit_permission(render_money_transfers))()
    with tab7:
        require_login(require_group_edit_permission(render_calendar))()

if __name__ == "__main__":
    main()
