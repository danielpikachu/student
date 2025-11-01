import streamlit as st
# 导入根目录的Google Sheet工具类（根目录直接导入）
from google_sheet_utils import GoogleSheetHandler

# 导入modules文件夹下的5个模块（注意文件夹名称大小写，通常为小写modules）
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups

# 页面基础配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化系统（Google Sheet连接 + 数据加载）
def initialize_system():
    if 'initialized' not in st.session_state:
        # 1. 初始化Google Sheet工具类（自动读取根目录的credentials.json）
        st.session_state.gsheet_handler = GoogleSheetHandler()
        st.session_state.gsheet_connected = False
        
        try:
            # 测试连接：尝试获取第一个分表（验证权限和连接）
            with st.spinner("正在连接Google Sheet..."):
                st.session_state.gsheet_handler.get_worksheet("Calendar")
                st.session_state.gsheet_connected = True
                st.success("✅ Google Sheet连接成功")
        except Exception as e:
            st.error(f"❌ Google Sheet连接失败: {str(e)}")
            st.info("将使用本地存储（数据不会同步到云端）")

        # 2. 定义所有模块的配置（分表名 <-> 会话状态数据键）
        modules_config = [
            {"sheet_name": "Calendar", "state_key": "calendar_events"},
            {"sheet_name": "Announcements", "state_key": "announcements"},
            {"sheet_name": "FinancialPlanning", "state_key": "financial_plans"},
            {"sheet_name": "MoneyTransfers", "state_key": "money_transfers"},
            {"sheet_name": "Groups", "state_key": "groups"}
        ]

        # 3. 加载数据（从Google Sheet或本地初始化）
        for module in modules_config:
            if st.session_state.gsheet_connected:
                # 从Google Sheet加载数据（调用工具类方法）
                st.session_state[module["state_key"]] = st.session_state.gsheet_handler.load_data(module["sheet_name"])
            else:
                # 本地模式：初始化空列表
                st.session_state[module["state_key"]] = []

        st.session_state.initialized = True

# 执行初始化
initialize_system()

# 主页面标题
st.title("🏛️ Student Council Management System")
st.markdown("统一管理学生会活动、财务、公告等核心业务")

# 侧边栏：数据同步控制
with st.sidebar:
    st.header("🔄 数据同步中心")
    
    if st.session_state.gsheet_connected:
        st.success("已连接到Google Sheet")
        
        # 批量同步所有模块数据到Google Sheet
        if st.button("同步所有数据到云端", use_container_width=True, type="primary"):
            with st.spinner("正在同步所有模块数据..."):
                modules_config = [
                    {"sheet_name": "Calendar", "state_key": "calendar_events"},
                    {"sheet_name": "Announcements", "state_key": "announcements"},
                    {"sheet_name": "FinancialPlanning", "state_key": "financial_plans"},
                    {"sheet_name": "MoneyTransfers", "state_key": "money_transfers"},
                    {"sheet_name": "Groups", "state_key": "groups"}
                ]
                # 调用工具类保存每个模块的数据
                for module in modules_config:
                    st.session_state.gsheet_handler.save_data(
                        module["sheet_name"], 
                        st.session_state[module["state_key"]]
                    )
                st.success("✅ 所有数据已同步到Google Sheet")
    else:
        st.warning("未连接到Google Sheet（仅本地存储）")
    
    st.markdown("---")
    st.subheader("模块导航")
    st.markdown("""
    - 📅 日程管理  
    - 📢 公告发布  
    - 📊 财务规划  
    - 💸 转账记录  
    - 👥 社团管理  
    """)
    st.markdown("---")
    st.info("© 2025 学生会管理系统")

# 创建选项卡（对应5个模块）
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 日程管理", 
    "📢 公告发布", 
    "📊 财务规划",
    "💸 转账记录",
    "👥 社团管理"
])

# 渲染各模块（传递工具类、分表名、数据键）
with tab1:
    render_calendar(
        gsheet_handler=st.session_state.gsheet_handler,
        sheet_name="Calendar",
        data_key="calendar_events"
    )

with tab2:
    render_announcements(
        gsheet_handler=st.session_state.gsheet_handler,
        sheet_name="Announcements",
        data_key="announcements"
    )

with tab3:
    render_financial_planning(
        gsheet_handler=st.session_state.gsheet_handler,
        sheet_name="FinancialPlanning",
        data_key="financial_plans"
    )

with tab4:
    render_money_transfers(
        gsheet_handler=st.session_state.gsheet_handler,
        sheet_name="MoneyTransfers",
        data_key="money_transfers"
    )

with tab5:
    render_groups(
        gsheet_handler=st.session_state.gsheet_handler,
        sheet_name="Groups",
        data_key="groups"
    )
