import streamlit as st
import hashlib

# 导入模块
from modules.Calendar import render_calendar
from modules.Groups import render_groups
from modules.MoneyTransfers import render_money_transfers

# 初始化会话状态
def init_session_state():
    # 用户相关
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = "member"
    if "users" not in st.session_state:
        # 用户名: 加密后的密码（示例：admin/admin123）
        st.session_state.users = {
            "admin": hashlib.sha256("admin123".encode()).hexdigest(),
            "member1": hashlib.sha256("member123".encode()).hexdigest()
        }

    # 日历事件
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {}
    if "current_month" not in st.session_state:
        today = st.date.today()
        st.session_state.current_month = (today.year, today.month)
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = st.date.today()

    # 群组数据
    if "groups" not in st.session_state:
        st.session_state.groups = []
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {}

    # 资金交易
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

# 密码验证
def authenticate_user(username, password):
    if username in st.session_state.users:
        return st.session_state.users[username] == hashlib.sha256(password.encode()).hexdigest()
    return False

# 权限判断
def is_admin():
    return st.session_state.user == "admin"

# 获取用户所属群组
def get_user_groups():
    return st.session_state.member_groups.get(st.session_state.user, ["未分配"])

def main():
    init_session_state()
    st.set_page_config(page_title="学生会管理系统", layout="wide")

    st.title("🏛️ 学生会管理系统")
    st.write("简化版应用 - 用于测试部署")
    st.divider()

    # 侧边栏登录
    with st.sidebar:
        st.header("用户登录")
        if st.session_state.user is None:
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("登录"):
                    if authenticate_user(username, password):
                        st.session_state.user = username
                        st.success("登录成功！")
                        st.rerun()  # 刷新页面
                    else:
                        st.error("用户名或密码错误")
            with col2:
                if st.button("重置"):
                    st.rerun()
        else:
            st.info(f"当前用户：{st.session_state.user}")
            st.info(f"角色：{'管理员' if is_admin() else '成员'}")
            if st.button("退出登录"):
                st.session_state.user = None
                st.success("已退出登录")
                st.rerun()

    # 登录后显示功能
    if st.session_state.user:
        tab1, tab2, tab3 = st.tabs(["📅 日历", "👥 群组", "💸 资金交易"])
        with tab1:
            render_calendar(is_admin())
        with tab2:
            render_groups(is_admin(), get_user_groups())
        with tab3:
            render_money_transfers(is_admin())
    else:
        st.warning("请先登录以使用系统功能")

if __name__ == "__main__":
    main()
