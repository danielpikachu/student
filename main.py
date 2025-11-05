import streamlit as st
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入工具类和功能模块
from google_sheet_utils import GoogleSheetHandler
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

# 初始化会话状态（采用命名空间隔离）
if 'initialized' not in st.session_state:
    # 日历模块命名空间
    st.session_state.calendar = {
        "events": [],
        "scheduled": [],
        "occasional": []
    }
    
    # 公告模块命名空间
    st.session_state.announcements = {
        "items": []
    }
    
    # 财务规划模块命名空间
    st.session_state.financial_planning = {
        "records": []
    }
    
    # 考勤模块命名空间
    st.session_state.attendance = {
        "events": [],
        "records": [],
        "members": []
    }
    
    # 转账模块命名空间
    st.session_state.money_transfers = {
        "records": [],
        "categories": [],
        "pending": []
    }
    
    # 群组模块命名空间
    st.session_state.groups = {
        "items": [],
        "members": []
    }
    
    st.session_state.initialized = True

# 主标题
st.title("Student Council Management System")

# 功能选项卡（保持原有顺序）
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "📋 Attendance",
    "💸 Money Transfers",
    "👥 Groups"
])

# 渲染各功能模块（传递模块命名空间前缀）
with tab1:
    render_calendar(namespace="calendar")
with tab2:
    render_announcements(namespace="announcements")
with tab3:
    render_financial_planning(namespace="financial_planning")
with tab4:
    render_attendance(namespace="attendance")
with tab5:
    render_money_transfers(namespace="money_transfers")
with tab6:
    render_groups(namespace="groups")

# 页脚信息
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
