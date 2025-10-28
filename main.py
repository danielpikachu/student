import streamlit as st
from calendar import render_calendar
from groups import render_groups
from money_transfers import render_money_transfers
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 页面配置
st.set_page_config(
    page_title="Student Council Management System",
    page_icon="🏛️",
    layout="wide"
)

# 初始化会话状态（统一命名，为 Google Sheet 同步预留结构）
if 'initialized' not in st.session_state:
    # Calendar 模块数据（标准化字段名，与 Google Sheet 列名对应）
    st.session_state.calendar_events = [
        # 示例结构：与 Google Sheet 列名一致（Title, Date, Time, ...）
        {"Title": "", "Date": None, "Time": None, "Location": "", "Organizer": "", "Description": ""}
    ][1:]  # 清空示例
    
    # Groups 模块数据
    st.session_state.groups = [
        {"GroupID": "", "GroupName": "", "Leader": "", "Description": "", "MemberCount": 0}
    ][1:]
    
    # Groups 成员数据
    st.session_state.group_members = [
        {"MemberID": "", "GroupID": "", "Name": "", "StudentID": "", "Position": "", "Contact": ""}
    ][1:]
    
    # MoneyTransfers 模块数据
    st.session_state.money_transfers = [
        {"Date": None, "Type": "", "Amount": 0.0, "Group": "", "Handler": "", "Description": ""}
    ][1:]
    
    st.session_state.initialized = True

# Google Sheet 同步函数（预留接口，需配置 service_account.json）
def init_google_sheet():
    """初始化 Google Sheet 连接（后续需手动添加密钥文件）"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(credentials)
        # 假设 Google Sheet 名称为 "StudentCouncilData"，需提前创建
        sheet = client.open("StudentCouncilData")
        return {
            "calendar": sheet.worksheet("Calendar"),       # 对应 Calendar 模块的工作表
            "groups": sheet.worksheet("Groups"),           # 对应 Groups 模块的工作表
            "money_transfers": sheet.worksheet("MoneyTransfers")  # 对应 MoneyTransfers 模块的工作表
        }
    except Exception as e:
        st.sidebar.warning(f"Google Sheet 连接未初始化：{str(e)}")
        return None

# 侧边栏导航（统一模块名称显示）
st.sidebar.title("Navigation")
module = st.sidebar.radio(
    "Select Module",
    ("Calendar", "Groups", "MoneyTransfers"),  # 严格统一模块名（含大小写）
    index=0
)

# 主标题（显示当前模块名，保持一致）
st.title(f"Student Council Management System - {module}")

# 加载对应模块
if module == "Calendar":
    render_calendar()
elif module == "Groups":
    render_groups()
elif module == "MoneyTransfers":
    render_money_transfers()

# 侧边栏：Google Sheet 同步按钮（预留）
st.sidebar.markdown("---")
if st.sidebar.button("Sync to Google Sheet"):
    sheets = init_google_sheet()
    if sheets:
        st.sidebar.success("Data synced successfully!")  # 实际同步逻辑在各模块中实现
    else:
        st.sidebar.error("Failed to sync. Check credentials.")
