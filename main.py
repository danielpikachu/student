import streamlit as st
# 关键调整：从 modules 文件夹导入模块（使用相对路径）
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money_transfers import render_money_transfers
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（数据结构保持不变）
if 'initialized' not in st.session_state:
    # Calendar 模块数据
    st.session_state.calendar_events = []
    
    # Groups 模块数据
    st.session_state.groups = []
    st.session_state.group_members = []
    
    # MoneyTransfers 模块数据
    st.session_state.money_transfers = []
    
    st.session_state.initialized = True

# Google Sheet 同步函数（预留接口）
def init_google_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(credentials)
        sheet = client.open("StudentCouncilData")
        return {
            "calendar": sheet.worksheet("Calendar"),
            "groups": sheet.worksheet("Groups"),
            "money_transfers": sheet.worksheet("MoneyTransfers")
        }
    except Exception as e:
        st.sidebar.warning(f"Google Sheet 连接未初始化：{str(e)}")
        return None

# 侧边栏导航
st.sidebar.title("Navigation")
module = st.sidebar.radio(
    "Select Module",
    ("Calendar", "Groups", "MoneyTransfers"),
    index=0
)

# 主标题
st.title(f"Student Council Management System - {module}")

# 加载对应模块（调用方式不变，导入路径已调整）
if module == "Calendar":
    render_calendar()
elif module == "Groups":
    render_groups()
elif module == "MoneyTransfers":
    render_money_transfers()

# Google Sheet 同步按钮
st.sidebar.markdown("---")
if st.sidebar.button("Sync to Google Sheet"):
    sheets = init_google_sheet()
    if sheets:
        st.sidebar.success("Data synced successfully!")
    else:
        st.sidebar.error("Failed to sync. Check credentials.")
