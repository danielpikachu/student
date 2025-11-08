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
# 初始化Google Sheet处理器
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
        return
    try:
        gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
    except:
        try:
            header = ["username", "password", "register_time", "last_login"]
            spreadsheet = gs_handler.client.open(SHEET_NAME)
            spreadsheet.add_worksheet(title=USER_SHEET_TAB, rows=100, cols=4)
            worksheet = spreadsheet.worksheet(USER_SHEET_TAB)
            worksheet.append_row(header)
        except:
            pass

def get_user_by_username(username):
    if not gs_handler:
        return None
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except:
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
    if not gs_handler or get_user_by_username(username):
        return False
    hashed_pwd = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_user = [username, hashed_pwd, now, now]
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        worksheet.append_row(new_user)
        return True
    except:
        return False

def update_user_last_login(username):
    if not gs_handler:
        return False
    init_user_sheet()
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except:
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
            except:
                return False
    return False

# ---------------------- 会话状态初始化 ----------------------
def init_session_state():
    # 确保所有模块需要的状态都被初始化
    required_states = {
        # 系统配置
        "sys_admin_password": "sc_admin_2025",
        # 认证相关
        "auth_logged_in": False,
        "auth_username": "",
        "auth_is_admin": False,
        # 日历模块
        "cal_events": [],
        "cal_current_month": datetime.today().replace(day=1),
        # 公告模块
        "ann_list": [],
        # 考勤模块
        "att_members": [],
        "att_meetings": [],
        "att_records": {},
        # 财务规划模块 - 修复关键缺失状态
        "fin_current_funds": 0.0,
        "fin_annual_target": 15000.0,
        "fin_scheduled_events": [],  # 关键修复
        "fin_occasional_events": [],  # 关键修复
        # 转账模块
        "tra_records": [],
        # 群组模块
        "grp_list": [],
        "grp_members": [],
        # 权限控制标记
        "initialized": True
    }
    
    # 初始化所有缺失的状态
    for key, value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ---------------------- 核心权限控制（强制隐藏编辑内容） ----------------------
def require_login(func):
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper

def hide_editor_for_non_admin(func):
    """强制隐藏普通用户的编辑内容（通过捕获输出实现）"""
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_is_admin:
            # 普通用户：使用容器捕获并过滤编辑内容
            with st.container():
                # 先显示查看提示
                st.info("普通用户仅可查看内容，无编辑权限")
                # 创建编辑区域占位符（用于覆盖）
                edit_container = st.container()
                with edit_container:
                    # 执行原始函数但捕获输出
                    func(*args, **kwargs)
                # 关键：用空内容覆盖编辑区域（假设编辑内容在最后）
                edit_container.empty()
        else:
            # 管理员：显示全部内容
            func(*args, **kwargs)
    return wrapper

# ---------------------- 登录注册界面 ----------------------
def show_login_register_form():
    with st.container():
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            st.subheader("用户登录")
            username = st.text_input("用户名", key="login_username")
            password = st.text_input("密码", type="password", key="login_password")
            
            if st.button("登录", use_container_width=True):
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
                
                # 管理员判断（仅Secrets中的用户）
                is_admin = username in st.secrets.get("admin_users", [])
                
                # 更新会话状态
                st.session_state.auth_logged_in = True
                st.session_state.auth_username = username
                st.session_state.auth_is_admin = is_admin
                
                update_user_last_login(username)
                st.success("登录成功，正在加载...")
                st.rerun()
        
        with tab2:
            st.subheader("用户注册")
            new_username = st.text_input("用户名", key="reg_username")
            new_password = st.text_input("密码", type="password", key="reg_password")
            confirm_password = st.text_input("确认密码", type="password", key="reg_confirm_pwd")
            
            if st.button("注册", use_container_width=True):
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
    
    # 初始化所有会话状态（确保无缺失）
    init_session_state()
    
    # 未登录时显示登录界面
    if not st.session_state.auth_logged_in:
        st.title("📝 学生理事会管理系统 - 登录")
        show_login_register_form()
        return
    
    # 已登录主界面
    with st.container():
        st.title("Student Council Management System")
        
        # 侧边栏用户信息
        with st.sidebar:
            st.markdown("---")
            user_data = get_user_by_username(st.session_state.auth_username)
            last_login = user_data['last_login'] if (user_data and 'last_login' in user_data) else '无法获取'
            
            st.info(f"""
            👤 当前用户：{st.session_state.auth_username}  
            📌 身份：{'管理员' if st.session_state.auth_is_admin else '普通用户'}  
            🕒 最后登录：{last_login}
            """)
            if st.button("退出登录", use_container_width=True):
                # 重置状态
                st.session_state.auth_logged_in = False
                st.session_state.auth_username = ""
                st.session_state.auth_is_admin = False
                st.rerun()
            st.markdown("---")
            st.info("© 2025 Student Council Management System")
        
        # 功能选项卡
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📅 Calendar", "📢 Announcements", "💰 Financial Planning",
            "📋 Attendance", "💸 Money Transfers", "👥 Groups"
        ])
        
        # 渲染模块（强制控制普通用户编辑内容）
        with tab1:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_calendar()
            render()
        
        with tab2:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_announcements()
            render()
        
        with tab3:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_financial_planning()
            render()
        
        with tab4:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_attendance()
            render()
        
        with tab5:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_money_transfers()
            render()
        
        with tab6:
            @require_login
            @hide_editor_for_non_admin
            def render():
                render_groups()
            render()

if __name__ == "__main__":
    main()
