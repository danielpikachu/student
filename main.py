import streamlit as st
# 导入模块（匹配新文件名，注意：文件名含空格需用importlib，建议避免空格）
from modules.Calendar import render_calendar
from modules.Groups import render_groups
from modules.MoneyTransfers import render_money_transfers  # 无空格文件名更安全

# 初始化会话状态
def init_session_state():
    # 用户角色
    if "user_role" not in st.session_state:
        st.session_state.user_role = "member"
    
    # 日历事件
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {}
    
    # 群组数据
    if "groups" not in st.session_state:
        st.session_state.groups = []
    
    # 成员-群组关联
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {}
    
    # 资金交易记录
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

# 判断管理员权限
def is_admin():
    return st.session_state.user == "admin"

# 获取用户所属群组
def get_user_group():
    return st.session_state.member_groups.get(st.session_state.user, "未分配")

def main():
    init_session_state()
    
    st.set_page_config(
        page_title="学生会管理系统",
        layout="centered"
    )
    
    st.title("🏛️ 学生会管理系统")
    st.write("简化版应用 - 用于测试部署")
    st.divider()
    
    # 侧边栏用户登录
    with st.sidebar:
        st.header("用户登录")
        st.session_state.user = st.text_input("输入用户名", "admin")
        st.info(f"角色：{'管理员' if is_admin() else '成员'}")
    
    # 主标签页（匹配新模块名）
    tab1, tab2, tab3 = st.tabs(["📅 Calendar", "👥 Groups", "💸 Money Transfers"])
    
    with tab1:
        render_calendar(is_admin())  # 调用Calendar模块
    
    with tab2:
        render_groups(is_admin(), get_user_group())  # 调用Groups模块
    
    with tab3:
        render_money_transfers(is_admin())  # 调用MoneyTransfers模块

if __name__ == "__main__":
    main()
