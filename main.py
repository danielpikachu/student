import streamlit as st
import sys
import os
import hashlib
from datetime import datetime
# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler
# 导入功能模块
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.attendance import render_attendance
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# ---------------------- 全局配置 ----------------------
SHEET_NAME = "Student"
USER_SHEET_TAB = "users"
# 初始化Google Sheet处理器并添加错误处理
try:
    gs_handler = GoogleSheetHandler(credentials_path="")
except Exception as e:
    gs_handler = None
    st.error(f"Google Sheets初始化失败: {str(e)}")

# ---------------------- 密码加密工具 ----------------------
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# ---------------------- 用户数据操作 ----------------------
def init_user_sheet():
    if not gs_handler:
        st.error("Google Sheets连接未初始化，无法操作用户数据")
        return
    
    try:
        gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
    except Exception as e:
        try:
            header = ["username", "password", "register_time", "last_login"]
            spreadsheet = gs_handler.client.open(SHEET_NAME)
            spreadsheet.add_worksheet(title=USER_SHEET_TAB, rows=100, cols=4)
            worksheet = spreadsheet.worksheet(USER_SHEET_TAB)
            worksheet.append_row(header)
        except Exception as create_err:
            st.error(f"创建用户表失败: {str(create_err)}")

def get_user_by_username(username):
    if not gs_handler:
        return None
    
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"获取用户数据失败: {str(e)}")
        return None
    
    if not data:
        return None
    for row in data[1:]:
        if row[0] == username:
            return {
                "username": row[0],
                "password": row[1],
                "register_time": row[2],
                "last_login": row[3]
            }
    return None

def add_new_user(username, password):
    if not gs_handler:
        st.error("Google Sheets连接未初始化，无法注册用户")
        return False
        
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
        st.error(f"添加用户失败: {str(e)}")
        return False

def update_user_last_login(username):
    if not gs_handler:
        return False
        
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"获取用户数据失败: {str(e)}")
        return False
    
    if not data:
        return False
    for i, row in enumerate(data[1:]):
        if row[0] == username:
            row_num = i + 2
            new_last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                worksheet.update_cell(row_num, 4, new_last_login)
                return True
            except Exception as e:
                st.error(f"更新登录时间失败: {str(e)}")
                return False
    return False

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

# ---------------------- 核心权限控制装饰器 ----------------------
def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper

def require_edit_permission(func):
    """普通用户完全隐藏编辑内容，管理员显示全部"""
    def wrapper(*args, **kwargs):
        # 向模块传递权限标识，模块需根据此参数控制编辑元素显示
        return func(*args,** kwargs, show_editor=st.session_state.auth_is_admin)
    return wrapper

def require_group_edit_permission(func):
    """群组模块同样仅管理员显示编辑内容"""
    def wrapper(*args, **kwargs):
        # 无论输入什么访问码，普通用户都不显示编辑内容
        return func(*args, **kwargs, show_editor=st.session_state.auth_is_admin)
    return wrapper

# ---------------------- 登录注册界面 ----------------------
def show_login_register_form():
    if not gs_handler:
        st.warning("注意：Google Sheets连接未初始化，登录功能可能无法正常使用")
    
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        st.subheader("用户登录")
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("登录"):
            if not gs_handler:
                st.error("Google Sheets连接未初始化，无法登录")
                return
                
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
            
            # 关键：仅Secrets中配置的用户才是管理员
            is_admin = username in st.secrets.get("admin_users", [])
            
            st.session_state.auth_logged_in = True
            st.session_state.auth_username = username
            st.session_state.auth_is_admin = is_admin
            
            update_user_last_login(username)
            
            st.success(f"登录成功！欢迎回来，{'管理员' if is_admin else '用户'} {username}！")
            st.rerun()
    
    with tab2:
        st.subheader("用户注册")
        new_username = st.text_input("用户名", key="reg_username")
        new_password = st.text_input("密码", type="password", key="reg_password")
        confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_pwd")
        
        if st.button("注册"):
            if not gs_handler:
                st.error("Google Sheets连接未初始化，无法注册")
                return
                
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

# ---------------------- 页面主逻辑 ----------------------
def main():
    st.set_page_config(
        page_title="Student Council Management System",
        page_icon="🏛️",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.auth_logged_in:
        st.title("📝 学生理事会管理系统 - 登录")
        show_login_register_form()
        return
    
    st.title("Student Council Management System")
    
    with st.sidebar:
        st.markdown("---")
        st.info(f"""
        👤 当前用户：{st.session_state.auth_username}  
        📌 身份：{'管理员' if st.session_state.auth_is_admin else '普通用户'}  
        🕒 最后登录：{get_user_by_username(st.session_state.auth_username)['last_login'] if gs_handler else '无法获取'}
        """)
        if st.button("退出登录"):
            st.session_state.auth_logged_in = False
            st.session_state.auth_username = ""
            st.session_state.auth_is_admin = False
            st.session_state.auth_current_group_code = ""
            st.rerun()
        st.markdown("---")
        st.info("© 2025 Student Council Management System")
    
    # 功能选项卡
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Calendar", "📢 Announcements", "💰 Financial Planning",
        "📋 Attendance", "💸 Money Transfers", "👥 Groups"
    ])
    
    # 渲染模块（通过show_editor参数控制编辑内容显示）
    with tab1:
        require_login(require_edit_permission(render_calendar))()
    with tab2:
        require_login(require_edit_permission(render_announcements))()
    with tab3:
        require_login(require_edit_permission(render_financial_planning))()
    with tab4:
        require_login(require_edit_permission(render_attendance))()
    with tab5:
        require_login(require_edit_permission(render_money_transfers))()
    with tab6:
        require_login(require_group_edit_permission(render_groups))()

if __name__ == "__main__":
    main()
