import streamlit as st
# 从 modules 文件夹导入模块
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money_transfers import render_money_transfers

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（存储所有模块数据）
if 'initialized' not in st.session_state:
    # Calendar 模块数据
    st.session_state.calendar_events = []
    
    # Groups 模块数据
    st.session_state.groups = []
    st.session_state.group_members = []
    
    # MoneyTransfers 模块数据
    st.session_state.money_transfers = []
    
    st.session_state.initialized = True

# 主标题
st.title("Student Council Management System")

# 创建三个选项卡，对应三个模块（核心设计）
tab1, tab2, tab3 = st.tabs(["📅 Calendar", "👥 Groups", "💸 Money Transfers"])

# 在每个选项卡中渲染对应模块
with tab1:
    render_calendar()

with tab2:
    render_groups()

with tab3:
    render_money_transfers()

# 页脚
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
