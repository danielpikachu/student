import streamlit as st
import sys
import os
import pandas as pd  # 用于读取Excel文件处理

# 解决根目录模块导入问题
# 获取当前文件（main.py）所在目录（即根目录）
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# 将根目录添加到系统路径（确保能导入google_sheet_utils）
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类（根目录）
from google_sheet_utils import GoogleSheetHandler

# 导入功能模块（新增Attendance模块）
from modules.calendar import render_calendar
from modules.announcements import render_announcements
from modules.financial_planning import render_financial_planning
from modules.money_transfers import render_money_transfers
from modules.groups import render_groups
from modules.attendance import render_attendance  # 新增考勤模块导入

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
    # 新增考勤相关会话状态
    st.session_state.attendance_events = []
    st.session_state.attendance_records = []
    st.session_state.members = []  # 成员列表
    
    # 启动时自动加载根目录的members.xlsx
    member_file_path = os.path.join(ROOT_DIR, "members.xlsx")
    if os.path.exists(member_file_path):
        try:
            df = pd.read_excel(member_file_path)
            st.session_state.members = df.to_dict('records')
            st.success(f"成功加载成员列表：共 {len(st.session_state.members)} 人")
        except Exception as e:
            st.warning(f"加载成员列表失败：{str(e)}")
    else:
        st.info("未找到members.xlsx文件，成员列表为空")
    
    st.session_state.initialized = True  # 标记初始化完成

# 主标题
st.title("Student Council Management System")

# 功能选项卡（添加Attendance选项卡）
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "📋 Attendance",  # 新增考勤选项卡
    "💸 Money Transfers",
    "👥 Groups"
])

# 渲染各功能模块（添加考勤模块渲染）
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
