import streamlit as st
# 从 modules 文件夹导入模块（新增 announcements 模块）
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money_transfers import render_money_transfers
from modules.announcements import render_announcements  # 新增：导入公告模块

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（存储所有模块数据，新增 announcements 初始化）
if 'initialized' not in st.session_state:
    # Calendar 模块数据
    st.session_state.calendar_events = []
    
    # Groups 模块数据
    st.session_state.groups = []
    st.session_state.group_members = []
    
    # MoneyTransfers 模块数据
    st.session_state.money_transfers = []

    # 新增：Announcements 模块数据（存储公告列表）
    st.session_state.announcements = []
    
    st.session_state.initialized = True

# 主标题
st.title("Student Council Management System")

# 创建选项卡（新增 "Announcements" 选项卡，对应四个核心模块）
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Calendar", 
    "👥 Groups", 
    "💸 Money Transfers", 
    "📢 Announcements"  # 新增：公告选项卡
])

# 在每个选项卡中渲染对应模块（新增 tab4 渲染公告模块）
with tab1:
    render_calendar()
with tab2:
    render_groups()
with tab3:
    render_money_transfers()
with tab4:  # 新增：渲染公告模块
    render_announcements()

# 页脚
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
