import streamlit as st
# 导入模块（新增FinancialPlanning）
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

# 初始化会话状态
if 'initialized' not in st.session_state:
    st.session_state.calendar_events = []
    st.session_state.announcements = []
    st.session_state.financial_records = []  # 保留原财务记录（若需兼容旧数据）
    st.session_state.scheduled_events = []   # 新增：定期事件数据
    st.session_state.occasional_events = []  # 新增：临时事件数据
    st.session_state.money_transfers = []
    st.session_state.groups = []
    st.session_state.group_members = []
    st.session_state.initialized = True

# 主标题
st.title("Student Council Management System")

# 选项卡顺序：Calendar → Announcements → Financial Planning → Money Transfers → Groups
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "💸 Money Transfers",
    "👥 Groups"
])

# 渲染各模块
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

# 页脚
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
