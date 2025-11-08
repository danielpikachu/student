import streamlit as st
import sys
import os
import hashlib
from datetime import datetime
# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类（先导入原始类）
from google_sheet_utils import GoogleSheetHandler as OriginalGoogleSheetHandler
# 导入功能模块
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.attendance import render_attendance
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups
# ---------------------- 核心修复：包装GoogleSheetHandler，拦截写操作（双重保险） ----------------------
class PermissionedGoogleSheetHandler(OriginalGoogleSheetHandler):
    """带权限控制的Google Sheet处理器，拦截普通用户的写操作"""
    def __init__(self, credentials_path, scope=None):
        super().__init__(credentials_path, scope)
    
    # 拦截：追加单行数据
    def append_record(self, worksheet, data):
        if st.session_state.get("auth_allow_edit", False):
            return super().append_record(worksheet, data)
        else:
            return None
    
    # 拦截：追加多行数据
    def append_rows(self, worksheet, data):
        if st.session_state.get("auth_allow_edit", False):
            return worksheet.append_rows(data)
        else:
            return None
    
    # 拦截：更新单元格
    def update_cell(self, worksheet, row, col, value):
        if st.session_state.get("auth_allow_edit", False):
            return worksheet.update_cell(row, col, value)
        else:
            return None
    
    # 拦截：删除行
    def delete_record_by_value(self, worksheet, value):
        if st.session_state.get("auth_allow_edit", False):
            return super().delete_record_by_value(worksheet, value)
        else:
            return False
    
    # 拦截：清空工作表
    def clear_worksheet(self, worksheet):
        if st.session_state.get("auth_allow_edit", False):
            return worksheet.clear()
        else:
            return None
    
    # 拦截：写入工作表（新增方法的拦截）
    def write_sheet(self, spreadsheet_name, worksheet_name, data):
        if st.session_state.get("auth_allow_edit", False):
            return super().write_sheet(spreadsheet_name, worksheet_name, data)
        else:
            return None
# ---------------------- 核心功能：注入CSS隐藏编辑组件（精准匹配，不影响模块切换） ----------------------
def inject_edit_hide_css():
    """注入CSS样式，仅隐藏编辑相关组件，保留模块标签页和查看功能"""
    if not st.session_state.get("auth_allow_edit", False):
        st.markdown("""
        <style>
        /* 1. 隐藏所有编辑类按钮（精准排除保留按钮） */
        button:not(
            [aria-label="退出登录"], 
            [aria-label="🔄 同步数据"],
            [data-testid="stTab"] button,  /* 保留标签页切换按钮 */
            [data-baseweb="tab"] button     /* 保留模块内子标签页按钮 */
        ) {
            display: none !important;
        }
        
        /* 2. 隐藏编辑类输入组件（不影响查看类展示） */
        input[type="text"],
        input[type="password"],
        input[type="number"],
        textarea,
        input[type="file"],
        div[data-baseweb="radio-group"],
        div[data-baseweb="select"],
        div[data-baseweb="date-input"],
        div[data-baseweb="checkbox"],
        
        /* 3. 隐藏表单和管理员操作面板 */
        div[role="form"],
        div[data-baseweb="expander"][aria-label*="Admin"],
        div[data-baseweb="expander"][aria-label*="管理"],
        div[data-baseweb="expander"][aria-label*="删除"],
        
        /* 4. 隐藏Groups模块未验证时的编辑区域 */
        div[data-testid="stSidebar"] div[data-baseweb="expander"][aria-label="🔑 Group访问验证"] {
            display: none !important;
        }
        
        /* 5. 禁用数字输入框的增减按钮（仅隐藏，不影响查看） */
        input[type="number"]::-webkit-inner-spin-button,
        input[type="number"]::-webkit-outer-spin-button {
            display: none !important;
        }
        
        /* 6. 确保标签页正常显示（防止被误隐藏） */
        div[data-testid="stTabs"],
        div[data-baseweb="tabs"],
        div[data-baseweb="tab-list"],
        div[data-baseweb="tab"] {
            display: flex !important;
            visibility: visible !important;
        }
        </style>
        """, unsafe_allow_html=True)
# ---------------------- 全局配置 ----------------------
# Google Sheet配置
SHEET_NAME = "Student"
USER_SHEET_TAB = "users"
# 初始化带权限控制的Google Sheet处理器（替换原始处理器）
try:
    gs_handler = PermissionedGoogleSheetHandler(credentials_path="")
except Exception as e:
    st.error(f"Google Sheet初始化失败: {str(e)}")
    gs_handler = None
# ---------------------- 密码加密工具 ----------------------
def hash_password(password):
    """密码MD5加密（简单安全方案）"""
    return hashlib.md5(password.encode()).hexdigest()
# ---------------------- 用户数据操作 ----------------------
def init_user_sheet():
    """初始化用户表结构（如果不存在）"""
    if not gs_handler:
        st.error("Google Sheet未初始化，无法创建用户表")
        return False
    try:
        # 检查用户表是否存在（使用正确的get_worksheet方法）
        gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        return True
    except:
        try:
            # 创建用户表：用户名、加密密码、注册时间、最后登录时间
            header = ["username", "password", "register_time", "last_login"]
            # 创建新工作表并写入表头（使用权限控制的方法）
            spreadsheet = gs_handler.client.open(SHEET_NAME)
            spreadsheet.add_worksheet(title=USER_SHEET_TAB, rows=100, cols=4)
            worksheet = spreadsheet.worksheet(USER_SHEET_TAB)
            gs_handler.append_record(worksheet, header)
            return True
        except Exception as e:
            st.error(f"创建用户表失败: {str(e)}")
            return False
def get_user_by_username(username):
    """根据用户名查询用户（修复异常处理和Sheet连接）"""
    if not gs_handler:
        return None
    # 初始化用户表（失败则直接返回）
    if not init_user_sheet():
        return None
    try:
        # 获取工作表对象
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        # 获取所有行数据（包含表头）
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"获取用户数据失败: {str(e)}")
        return None
    
    if not data or len(data) < 2:
        return None
    # 跳过表头查询
    for row in data[1:]:
        if len(row) >= 1 and row[0] == username:
            # 确保返回数据结构完整
            return {
                "username": row[0] if len(row) > 0 else "",
                "password": row[1] if len(row) > 1 else "",
                "register_time": row[2] if len(row) > 2 else "",
                "last_login": row[3] if len(row) > 3 else ""
            }
    return None
def add_new_user(username, password):
    """注册新用户"""
    if not gs_handler:
        st.error("Google Sheet未初始化，无法注册用户")
        return False
    if get_user_by_username(username):
        return False  # 用户名已存在
    # 加密密码
    hashed_pwd = hash_password(password)
    # 注册时间和最后登录时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 写入用户表（使用权限控制的方法）
    new_user = [username, hashed_pwd, now, now]
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        gs_handler.append_record(worksheet, new_user)
        return True
    except Exception as e:
        st.error(f"添加用户失败: {str(e)}")
        return False
def update_user_last_login(username):
    """更新用户最后登录时间"""
    if not gs_handler:
        st.error("Google Sheet未初始化，无法更新登录时间")
        return False
    # 初始化用户表（失败则直接返回）
    if not init_user_sheet():
        return False
    try:
        worksheet = gs_handler.get_worksheet(SHEET_NAME, USER_SHEET_TAB)
        data = worksheet.get_all_values()
    except Exception as e:
        st.error(f"获取用户数据失败: {str(e)}")
        return False
    
    if not data or len(data) < 2:
        return False
    # 找到用户行并更新（使用权限控制的方法）
    for i, row in enumerate(data[1:]):
        if len(row) >= 1 and row[0] == username:
            # 计算实际行号（跳过表头+当前索引+1，因为工作表行号从1开始）
            row_num = i + 2
            new_last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 更新最后登录时间列（第4列，索引3）
            gs_handler.update_cell(worksheet, row_num, 4, new_last_login)
            return True
    return False
# ---------------------- 会话状态初始化 ----------------------
def init_session_state():
    """初始化所有会话状态（含用户认证相关）"""
    # 系统配置（sys_前缀）
    if "sys_admin_password" not in st.session_state:
        st.session_state.sys_admin_password = "sc_admin_2025"
    
    # 认证相关（auth_前缀）
    if "auth_logged_in" not in st.session_state:
        st.session_state.auth_logged_in = False
    if "auth_username" not in st.session_state:
        st.session_state.auth_username = ""
    if "auth_is_admin" not in st.session_state:
        st.session_state.auth_is_admin = False
    if "auth_current_group_code" not in st.session_state:
        st.session_state.auth_current_group_code = ""  # 存储当前验证的Group访问码
    # 核心权限标记：控制是否允许编辑
    if "auth_allow_edit" not in st.session_state:
        st.session_state.auth_allow_edit = False
    
    # 公告模块（ann_前缀）
    if "ann_list" not in st.session_state:
        st.session_state.ann_list = []
    
    # 日历模块（cal_前缀）
    if "cal_events" not in st.session_state:
        st.session_state.cal_events = []
    if "cal_current_month" not in st.session_state:
        st.session_state.cal_current_month = datetime.today().replace(day=1)
    
    # 考勤模块（att_前缀）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}
    
    # 财务规划模块（fin_前缀）
    if "fin_current_funds" not in st.session_state:
        st.session_state.fin_current_funds = 0.0
    if "fin_annual_target" not in st.session_state:
        st.session_state.fin_annual_target = 15000.0
    if "fin_scheduled_events" not in st.session_state:
        st.session_state.fin_scheduled_events = []
    if "fin_occasional_events" not in st.session_state:
        st.session_state.fin_occasional_events = []
    
    # 转账模块（tra_前缀）
    if "tra_records" not in st.session_state:
        st.session_state.tra_records = []
    
    # 群组模块（grp_前缀）
    if "grp_list" not in st.session_state:
        st.session_state.grp_list = []
    if "grp_members" not in st.session_state:
        st.session_state.grp_members = []
# ---------------------- 权限控制装饰器 ----------------------
def require_login(func):
    """登录校验装饰器：未登录则跳转至登录界面"""
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        return func(*args, **kwargs)
    return wrapper
def require_edit_permission(func):
    """编辑权限校验装饰器：控制非Groups模块的编辑权限"""
    def wrapper(*args, **kwargs):
        # 管理员：允许编辑
        if st.session_state.auth_is_admin:
            st.session_state.auth_allow_edit = True
            inject_edit_hide_css()
            result = func(*args, **kwargs)
            return result
        # 普通用户：禁止编辑，隐藏组件
        st.session_state.auth_allow_edit = False
        st.info("您是普通用户，仅拥有查看权限，无编辑权限。")
        inject_edit_hide_css()
        result = func(*args, **kwargs)
        return result
    return wrapper
def require_group_edit_permission(func):
    """Group模块编辑权限校验装饰器：控制Group模块的编辑权限"""
    def wrapper(*args, **kwargs):
        if st.session_state.auth_is_admin:
            # 管理员：允许编辑所有Group
            st.session_state.auth_allow_edit = True
            inject_edit_hide_css()
            result = func(*args, **kwargs)
            return result
        # 普通用户：单独处理访问码验证（不隐藏）
        st.session_state.auth_allow_edit = False
        st.warning("请先通过Group访问码验证，才能进行编辑操作。")
        
        # 注入CSS（先隐藏编辑组件）
        inject_edit_hide_css()
        
        # 重新显示访问码验证区域（覆盖CSS隐藏）
        st.markdown("""
        <style>
        div[data-testid="stSidebar"] div[data-baseweb="expander"][aria-label="🔑 Group访问验证"] {
            display: block !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 显示访问码验证表单
        with st.sidebar.expander("🔑 Group访问验证", expanded=True):
            access_code = st.text_input("请输入Group访问码", type="password")
            verify_btn = st.button("验证访问权限")
            
            if verify_btn:
                if access_code:
                    st.session_state.auth_current_group_code = access_code
                    st.session_state.auth_allow_edit = True
                    st.success("访问验证通过，可编辑当前Group！")
                    st.rerun()  # 重新渲染，显示编辑组件
                else:
                    st.error("请输入有效的访问码！")
                    st.session_state.auth_current_group_code = ""
                    st.session_state.auth_allow_edit = False
        
        result = func(*args, **kwargs)
        return result
    return wrapper
# ---------------------- 登录注册界面 ----------------------
def show_login_register_form():
    """显示登录注册表单"""
    # 登录注册界面不隐藏组件
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        st.subheader("用户登录")
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        
        if st.button("登录"):
            if not username or not password:
                st.error("用户名和密码不能为空！")
                return
            
            # 查询用户
            user = get_user_by_username(username)
            if not user:
                st.error("用户名不存在！")
                return
            
            # 验证密码
            hashed_pwd = hash_password(password)
            if user["password"] != hashed_pwd:
                st.error("密码错误！")
                return
            
            # 验证是否为管理员（从Secrets读取admin_users列表）
            is_admin = username in st.secrets.get("admin_users", [])
            
            # 更新会话状态
            st.session_state.auth_logged_in = True
            st.session_state.auth_username = username
            st.session_state.auth_is_admin = is_admin
            st.session_state.auth_allow_edit = is_admin  # 登录时直接设置编辑权限
            
            # 更新最后登录时间（忽略失败，不影响登录）
            update_user_last_login(username)
            
            st.success(f"登录成功！欢迎回来，{'管理员' if is_admin else '用户'} {username}！")
            st.rerun()
    
    with tab2:
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
            
            # 注册新用户
            success = add_new_user(new_username, new_password)
            if success:
                st.success("注册成功！请前往登录界面登录～")
            else:
                st.error("用户名已存在，请更换其他用户名！")
# ---------------------- 页面主逻辑 ----------------------
def main():
    # 页面配置
    st.set_page_config(
        page_title="Student Council Management System",
        page_icon="🏛️",
        layout="wide"
    )
    
    # 初始化会话状态
    init_session_state()
    
    # 未登录时显示登录注册界面
    if not st.session_state.auth_logged_in:
        st.title("📝 学生理事会管理系统 - 登录")
        show_login_register_form()
        return
    
    # 已登录时显示主界面
    st.title("Student Council Management System")
    
    # 侧边栏显示用户信息（修复空值异常）
    with st.sidebar:
        st.markdown("---")
        user_info = get_user_by_username(st.session_state.auth_username)
        last_login = user_info["last_login"] if user_info and user_info["last_login"] else "未记录"
        st.info(f"""
        👤 当前用户：{st.session_state.auth_username}  
        📌 身份：{'管理员' if st.session_state.auth_is_admin else '普通用户'}  
        🕒 最后登录：{last_login}
        """)
        if st.button("退出登录", key="logout_btn"):
            # 重置认证相关会话状态
            st.session_state.auth_logged_in = False
            st.session_state.auth_username = ""
            st.session_state.auth_is_admin = False
            st.session_state.auth_current_group_code = ""
            st.session_state.auth_allow_edit = False
            st.rerun()
        st.markdown("---")
        st.info("© 2025 Student Council Management System")
    
    # 功能选项卡（7大模块）- 确保标签页正常显示
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Calendar",
        "📢 Announcements",
        "💰 Financial Planning",
        "📋 Attendance",
        "💸 Money Transfers",
        "👥 Groups"
    ])
    
    # 装饰器顺序：先编辑权限（控制组件显示），后登录校验
    with tab1:
        require_edit_permission(require_login(render_calendar))()
    with tab2:
        require_edit_permission(require_login(render_announcements))()
    with tab3:
        require_edit_permission(require_login(render_financial_planning))()
    with tab4:
        require_edit_permission(require_login(render_attendance))()
    with tab5:
        require_edit_permission(require_login(render_money_transfers))()
    with tab6:
        require_group_edit_permission(require_login(render_groups))()
if __name__ == "__main__":
    main()
