import streamlit as st
import sys
import os
import hashlib
from datetime import datetime

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 模拟Google Sheets工具类和功能模块（实际使用时替换为真实逻辑）
class GoogleSheetHandler:
    def __init__(self, credentials_path=""):
        self.credentials_path = credentials_path
    def get_worksheet(self, sheet_name, tab_name):
        return None
    def append_row(self, row):
        pass
    def update_cell(self, row, col, value):
        pass
    def get_all_values(self):
        return []

def render_calendar():
    st.write("Calendar Module")
def render_announcements():
    st.write("Announcements Module")
def render_financial_planning():
    st.write("Financial Planning Module")
def render_attendance():
    st.write("Attendance Module")
def render_credit_rewards():
    st.write("Credit & Rewards Module")
def render_money_transfers():
    st.write("Money Transfers Module")
def render_groups():
    st.write("Groups Module")

# ---------------------- 全局配置 ----------------------
SHEET_NAME = "Student"
USER_SHEET_TAB = "users"
DEFAULT_ADMIN_USERS = ["admin", "root"]  # 默认管理员用户名
gs_handler = GoogleSheetHandler(credentials_path="")

# ---------------------- 密码加密工具 ----------------------
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# ---------------------- 用户数据操作 ----------------------
def init_user_sheet():
    try:
        gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
    except:
        header = ["username", "password", "register_time", "last_login"]
        # 模拟创建工作表逻辑
        pass

def get_user_by_username(username):
    init_user_sheet()
    try:
        # 模拟获取用户数据
        return {
            "username": username,
            "password": hash_password("test123"),
            "register_time": "2025-01-01 00:00:00",
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except:
        return None

def add_new_user(username, password):
    return True  # 模拟添加用户成功

def update_user_last_login(username):
    return True  # 模拟更新登录时间成功

# ---------------------- 会话状态初始化 ----------------------
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

# ---------------------- 权限控制装饰器 ----------------------
def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper

def require_edit_permission(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_is_admin:
            st.info("您没有编辑权限，只能查看内容")
        return func(*args, **kwargs)
    return wrapper

def require_group_edit_permission(func):
    def wrapper(*args, **kwargs):
        if st.session_state.auth_is_admin:
            return func(*args, **kwargs)
        with st.sidebar.expander("🔑 Group访问验证", expanded=True):
            access_code = st.text_input("请输入Group访问码", type="password")
            if st.button("验证访问权限"):
                if access_code:
                    st.session_state.auth_current_group_code = access_code
                    st.success("访问验证通过，可编辑当前Group！")
                else:
                    st.error("请输入有效的访问码！")
        return func(*args, **kwargs)
    return wrapper

# ---------------------- 登录注册界面 ----------------------
def show_login_register_form():
    with st.sidebar:
        st.markdown("---")
        st.subheader("用户登录")
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("登录"):
            if not username or not password:
                st.error("用户名和密码不能为空！")
                return
            
            user = get_user_by_username(username)
            if not user:
                st.error("用户名不存在！")
                return
            
            hashed_pwd = hash_password(password)
            if user["password"] != hashed_pwd:
                st.error("密码错误！")
                return
            
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
            st.success(f"登录成功！欢迎回来，{'管理员' if st.session_state.auth_is_admin else '用户'} {username}！")
            st.rerun()
        
        st.subheader("用户注册")
        new_username = st.text_input("用户名", key="reg_username")
        new_password = st.text_input("密码", type="password", key="reg_password")
        confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_pwd")
        
        if st.button("注册"):
            if not new_username or not new_password or not confirm_password:
                st.error("所有字段不能为空！")
                return
            
            if new_password != confirm_password:
                st.error("两次输入的密码不一致！")
                return
            
            if len(new_password) < 6:
                st.error("密码长度不能少于6位！")
                return
            
            success = add_new_user(new_username, new_password)
            if success:
                st.success("注册成功！请前往登录界面登录～")
            else:
                st.error("用户名已存在，请更换其他用户名！")
        st.markdown("---")

# ---------------------- 页面主逻辑 ----------------------
def main():
    st.set_page_config(
        page_title="Student Council Management System",
        page_icon="🏛️",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.auth_logged_in:
        st.title("Welcome to SCIS Student Council Management System")
        
        # 第二行提示文本
        st.markdown(
            """
            <div style="background-color: #f0f2f6; padding: 1.5rem; border-radius: 8px; text-align: center; margin: 0 2rem;">
                <p style="margin-bottom: 0.5rem;">Please log in using the form in the sidebar to access the Student Council management tools.</p>
                <p>If you don't have an account, please contact an administrator to create one for you.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 第三行功能标签（带图标）
        col1, col2, col3 = st.columns(3, gap="medium")
        with col1:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">📅</span>
                    <span>Event Planning</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">💰</span>
                    <span>Financial Management</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                """
                <div style="background-color: #e8f4f8; padding: 0.8rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.2rem;">🏆</span>
                    <span>Student Recognition</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # 显示登录注册表单（侧边栏）
        show_login_register_form()
        return
    
    st.title("Student Council Management System")
    
    with st.sidebar:
        st.markdown("---")
        st.info(f"""
        👤 当前用户：{st.session_state.auth_username}  
        📌 身份：{'管理员' if st.session_state.auth_is_admin else '普通用户'}  
        🕒 最后登录：{get_user_by_username(st.session_state.auth_username)['last_login']}
        """)
        if st.button("退出登录"):
            st.session_state.auth_logged_in = False
            st.session_state.auth_username = ""
            st.session_state.auth_is_admin = False
            st.session_state.auth_current_group_code = ""
            st.rerun()
        st.markdown("---")
        st.info("© 2025 Student Council Management System")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 Calendar", "📢 Announcements", "💰 Financial Planning",
        "📋 Attendance","🎁 Credit & Rewards","💸 Money Transfers", "👥 Groups"
    ])
    
    with tab1:
        require_login(require_edit_permission(render_calendar))()
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
        require_login(require_group_edit_permission(render_groups))()

if __name__ == "__main__":
    main()
