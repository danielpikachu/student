import streamlit as st
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 导入功能模块（新增attendance模块）
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.attendance import render_attendance  # 新增考勤模块
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（添加考勤相关状态）
if 'initialized' not in st.session_state:
    st.session_state.calendar_events = []
    st.session_state.announcements = []
    st.session_state.financial_records = []
    st.session_state.scheduled_events = []
    st.session_state.occasional_events = []
    st.session_state.money_transfers = []
    st.session_state.groups = []
    st.session_state.group_members = []
    st.session_state.attendance_events = []  # 考勤事件
    st.session_state.attendance_records = []  # 考勤记录
    st.session_state.members = []  # 成员列表
    st.session_state.initialized = True

# 主标题
st.title("Student Council Management System")

# 功能选项卡（将Attendance放在Money Transfers左边）
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "📋 Attendance",  # 新增考勤选项卡
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
with tab4:  # 考勤模块
    render_attendance()
with tab5:
    render_money_transfers()
with tab6:
    render_groups()

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
