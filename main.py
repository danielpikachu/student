import streamlit as st
import sys
import os

# 解决根目录模块导入问题
# 获取当前文件（main.py）所在目录（即根目录）
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# 将根目录添加到系统路径（确保能导入google_sheet_utils）
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类（根目录）
from google_sheet_utils import GoogleSheetHandler

# 导入功能模块
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（首次运行时）
if 'initialized' not in st.session_state:
    st.session_state.calendar_events = []
    st.session_state.announcements = []
    st.session_state.financial_records = []
    st.session_state.scheduled_events = []
    st.session_state.occasional_events = []
    st.session_state.money_transfers = []
    st.session_state.groups = []
    st.session_state.group_members = []
    st.session_state.initialized = True  # 标记初始化完成

# 主标题
st.title("Student Council Management System")

# 功能选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
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
    render_money_transfers()
with tab5:
    render_groups()

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
