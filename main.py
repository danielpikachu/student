import streamlit as st
# 导入所有模块的渲染函数
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money_transfers import render_money_transfers
from modules.financial_planning import render_financial_planning  # 财务规划模块
from modules.announcements import render_announcements  # 公告模块
# Google Sheets 工具函数
from modules.google_sheets import initialize_google_sheets, sync_with_google_sheets

# 页面基础配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化所有会话状态和 Google Sheets 连接
def initialize_system():
    """统一初始化系统数据和 Google Sheets 连接"""
    if 'initialized' not in st.session_state:
        # 1. 初始化 Google Sheets 连接状态
        st.session_state.gsheets_connected = False
        try:
            with st.spinner("正在连接 Google Sheets..."):
                initialize_google_sheets()  # 建立连接
                st.session_state.gsheets_connected = True
            st.success("✅ Google Sheets 连接成功")
        except Exception as e:
            st.error(f"❌ Google Sheets 连接失败: {str(e)}")
            st.info("将使用本地存储模式（数据不会持久化到云端）")

        # 2. 定义所有模块的配置（名称 + 会话状态键名）
        modules_config = [
            {"name": "calendar", "state_key": "calendar_events"},
            {"name": "groups", "state_key": "groups"},
            {"name": "money_transfers", "state_key": "money_transfers"},
            {"name": "financial_planning", "state_key": "financial_plans"},  # 财务规划
            {"name": "announcements", "state_key": "announcements"}  # 公告
        ]

        # 3. 从 Google Sheets 加载数据（或初始化本地数据）
        for module in modules_config:
            if st.session_state.gsheets_connected:
                # 从云端加载数据
                st.session_state[module["state_key"]] = sync_with_google_sheets(module["name"])
            else:
                # 本地初始化空数据
                st.session_state[module["state_key"]] = []

        # 标记初始化完成
        st.session_state.initialized = True

# 执行系统初始化
initialize_system()

# 主页面标题
st.title("🏛️ Student Council Management System")
st.markdown("统一管理学生会活动、财务、公告等核心业务")

# 侧边栏：数据同步控制
with st.sidebar:
    st.header("🔄 数据同步中心")
    
    # 显示连接状态
    if st.session_state.gsheets_connected:
        st.success("已连接到 Google Sheets")
        # 同步按钮（批量同步所有模块）
        if st.button("同步所有数据到云端", use_container_width=True, type="primary"):
            with st.spinner("正在同步所有模块数据..."):
                # 同步每个模块的数据
                modules_config = [
                    {"name": "calendar", "state_key": "calendar_events"},
                    {"name": "groups", "state_key": "groups"},
                    {"name": "money_transfers", "state_key": "money_transfers"},
                    {"name": "financial_planning", "state_key": "financial_plans"},
                    {"name": "announcements", "state_key": "announcements"}
                ]
                for module in modules_config:
                    sync_with_google_sheets(
                        module["name"], 
                        st.session_state[module["state_key"]]
                    )
                st.success("✅ 所有数据已同步到 Google Sheets")
    else:
        st.warning("未连接到 Google Sheets（仅本地存储）")
    
    st.markdown("---")
    st.subheader("模块导航")
    st.markdown("""
    - 📅 日程管理  
    - 👥 社团管理  
    - 💸 转账记录  
    - 📊 财务规划  
    - 📢 公告发布  
    """)
    st.markdown("---")
    st.info("© 2025 学生会管理系统")

# 创建选项卡（包含所有模块）
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 日程管理", 
    "👥 社团管理", 
    "💸 转账记录",
    "📊 财务规划",  # 新增财务规划选项卡
    "📢 公告发布"   # 新增公告选项卡
])

# 渲染各模块
with tab1:
    render_calendar()

with tab2:
    render_groups()

with tab3:
    render_money_transfers()

with tab4:  # 财务规划模块
    render_financial_planning()

with tab5:  # 公告模块
    render_announcements()
