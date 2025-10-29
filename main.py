import streamlit as st
# 从 modules 文件夹导入所有模块（导入顺序不影响功能，仅主程序选项卡顺序决定显示次序）
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# 页面基础配置（保持原有设置不变）
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（存储所有模块数据，确保所有模块的初始数据都已定义）
if 'initialized' not in st.session_state:
    # Calendar 模块数据：存储日历事件列表
    st.session_state.calendar_events = []
    
    # Announcements 模块数据：存储公告列表（新增模块的初始数据）
    st.session_state.announcements = []
    
    # MoneyTransfers 模块数据：存储转账记录列表
    st.session_state.money_transfers = []
    
    # Groups 模块数据：存储社团列表和社团成员列表
    st.session_state.groups = []
    st.session_state.group_members = []
    
    # 标记初始化完成（避免重复初始化）
    st.session_state.initialized = True

# 系统主标题（保持不变）
st.title("Student Council Management System")

# 核心修改：按「Calendar → Announcements → Money Transfers → Groups」顺序创建选项卡
# 选项卡变量（tab1~tab4）与模块一一对应，顺序直接决定前端显示次序
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Calendar",          # 第1个选项卡：日历模块
    "📢 Announcements",     # 第2个选项卡：公告模块（调整后位置）
    "💸 Money Transfers",   # 第3个选项卡：转账模块（调整后位置）
    "👥 Groups"             # 第4个选项卡：社团模块（调整后位置）
])

# 为每个选项卡绑定对应的模块渲染函数（顺序与选项卡创建顺序严格一致）
with tab1:
    # 第1个选项卡：渲染日历模块
    render_calendar()

with tab2:
    # 第2个选项卡：渲染公告模块
    render_announcements()

with tab3:
    # 第3个选项卡：渲染转账模块
    render_money_transfers()

with tab4:
    # 第4个选项卡：渲染社团模块
    render_groups()

# 侧边栏页脚（保持原有版权信息不变）
st.sidebar.markdown("---")
st.sidebar.info("© 2025 Student Council Management System")
