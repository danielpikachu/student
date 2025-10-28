import streamlit as st
# 直接导入三个模块的核心功能
from calendar_module import render_calendar
from groups_module import render_groups
from money_module import render_money

# 页面配置
st.set_page_config(
    page_title="学生理事会管理系统",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（存储所有模块数据）
if 'init' not in st.session_state:
    # 日程数据
    st.session_state.calendar_events = []
    # 社团与成员数据
    st.session_state.groups = []
    st.session_state.members = []
    # 资金交易数据
    st.session_state.transactions = []
    st.session_state.init = True

# 侧边栏导航
st.sidebar.title("导航菜单")
module = st.sidebar.radio(
    "选择功能模块",
    ("日程管理", "社团管理", "资金管理"),
    index=0
)

# 主标题
st.title(f"学生理事会管理系统 - {module}")

# 加载对应模块
if module == "日程管理":
    render_calendar()
elif module == "社团管理":
    render_groups()
elif module == "资金管理":
    render_money()

# 页脚
st.sidebar.markdown("---")
st.sidebar.info("© 2025 学生理事会管理系统")
