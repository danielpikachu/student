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
    
    # 初始化编辑区域占位符（用于隐藏普通用户的编辑内容）
    if "edit_placeholders" not in st.session_state:
        st.session_state.edit_placeholders = {
            "calendar": st.empty(),
            "announcements": st.empty(),
            "financial": st.empty(),
            "attendance": st.empty(),
            "transfers": st.empty(),
            "groups": st.empty()
        }

# ---------------------- 核心权限控制装饰器 ----------------------
def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper

def require_edit_permission(module_name):
    """通过占位符隐藏普通用户的编辑内容，仅显示查看内容"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 先渲染模块内容（包含查看和编辑部分）
            func(*args, **kwargs)
            
            # 普通用户：清除编辑区域内容（假设编辑内容在特定位置）
            if not st.session_state.auth_is_admin:
                # 使用占位符覆盖编辑区域（实际场景可能需要调整选择器）
                with st.session_state.edit_placeholders[module_name]:
                    st.write("")  # 清空编辑区域
                st.info("普通用户仅可查看内容，无编辑权限")
        return wrapper
    return decorator

def require_group_edit_permission(func):
    """群组模块专用：普通用户隐藏编辑内容"""
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        
        if not st.session_state.auth_is_admin:
            with st.session_state.edit_placeholders["groups"]:
                st.write("")  # 清空编辑区域
            st.info("普通用户仅可查看内容，无编辑权限")
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
            
            # 仅Secrets中配置的用户才是管理员
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
        user_data = get_user_by_username(st.session_state.auth_username) if gs_handler else None
        last_login = user_data['last_login'] if (user_data and 'last_login' in user_data) else '无法获取'
        
        st.info(f"""
        👤 当前用户：{st.session_state.auth_username}  
        📌 身份：{'管理员' if st.session_state.auth_is_admin else '普通用户'}  
        🕒 最后登录：{last_login}
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
    
    # 渲染模块（为每个模块绑定专用占位符，用于隐藏编辑内容）
    with tab1:
        @require_login
        @require_edit_permission("calendar")
        def render():
            render_calendar()
        render()
    
    with tab2:
        @require_login
        @require_edit_permission("announcements")
        def render():
            render_announcements()
        render()
    
    with tab3:
        @require_login
        @require_edit_permission("financial")
        def render():
            render_financial_planning()
        render()
    
    with tab4:
        @require_login
        @require_edit_permission("attendance")
        def render():
            render_attendance()
        render()
    
    with tab5:
        @require_login
        @require_edit_permission("transfers")
        def render():
            render_money_transfers()
        render()
    
    with tab6:
        @require_login
        @require_group_edit_permission
        def render():
            render_groups()
        render()

if __name__ == "__main__":
    main()
