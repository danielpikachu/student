import streamlit as st

# 导入模块（确保modules文件夹下有这三个文件）
from modules.Calendar import render_calendar
from modules.Groups import render_groups
from modules.MoneyTransfers import render_money_transfers

# 初始化最基础的会话状态
def init_session_state():
    # 用户状态（简化登录，默认管理员）
    if "user" not in st.session_state:
        st.session_state.user = "admin"  # 直接默认登录管理员，跳过密码验证
    
    # 日历数据
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {}
    
    # 群组数据
    if "groups" not in st.session_state:
        st.session_state.groups = []
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {}
    
    # 交易数据
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

# 判断是否为管理员（简化：默认用户就是管理员）
def is_admin():
    return st.session_state.user == "admin"

# 获取用户群组（简化）
def get_user_groups():
    return st.session_state.member_groups.get(st.session_state.user, ["默认群组"])

def main():
    init_session_state()
    st.set_page_config(page_title="学生会管理系统", layout="wide")
    
    st.title("🏛️ 学生会管理系统")
    st.write("精简版 - 确保能运行")
    st.divider()
    
    # 简化登录状态显示（直接显示已登录）
    st.sidebar.info(f"当前用户：{st.session_state.user}（管理员）")
    
    # 主标签页
    tab1, tab2, tab3 = st.tabs(["📅 日历", "👥 群组", "💸 资金交易"])
    
    with tab1:
        render_calendar(is_admin())
    
    with tab2:
        render_groups(is_admin(), get_user_groups())
    
    with tab3:
        render_money_transfers(is_admin())

if __name__ == "__main__":
    main()
