import streamlit as st
import sys
import os
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

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# ---------------------- 统一会话状态初始化（命名空间隔离）----------------------
def init_session_state():
    """初始化所有模块的会话状态，使用模块前缀隔离"""
    # 系统配置（sys_前缀）
    if "sys_admin_password" not in st.session_state:
        st.session_state.sys_admin_password = "sc_admin_2025"  # 统一管理员密码存储
    
    # 公告模块（ann_前缀）
    if "ann_list" not in st.session_state:
        st.session_state.ann_list = []
    
    # 日历模块（cal_前缀）
    if "cal_events" not in st.session_state:
        st.session_state.cal_events = []
    if "cal_current_month" not in st.session_state:
        from datetime import datetime
        st.session_state.cal_current_month = datetime.today().replace(day=1)
    
    # 考勤模块（att_前缀）
    if "att_members" not in st.session_state:
        st.session_state.att_members = []  # 成员列表：[{id, name}]
    if "att_meetings" not in st.session_state:
        st.session_state.att_meetings = []  # 会议列表：[{id, name}]
    if "att_records" not in st.session_state:
        st.session_state.att_records = {}  # 考勤数据：{(member_id, meeting_id): bool}
    
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

# 初始化会话状态
init_session_state()

# 主标题
st.title("Student Council Management System")

# 功能选项卡
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "📋 Attendance",
    "💸 Money Transfers",
    "👥 Groups"
])

# 渲染各功能模块
with tab1:
    render_calendar()
with tab2:
    render_announcements()
with tab3:
    render_financial_planning()
with tab4:
    render_attendance()
with tab5:
    render_money_transfers()
with tab6:
    render_groups()

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
