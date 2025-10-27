import streamlit as st
# 导入模块（严格对应文件名）
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money import render_money

# 初始化会话状态
def init_session_state():
    # 用户角色
    if "user_role" not in st.session_state:
        st.session_state.user_role = "member"
    
    # 日历事件（calendar模块数据）
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {
            "2024-09-15": "迎新大会",
            "2024-10-01": "国庆活动"
        }
    
    # 群组数据（groups模块数据）
    if "groups" not in st.session_state:
        st.session_state.groups = ["主席团", "活动部", "财务部", "宣传部"]
    
    # 成员-群组关联
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {
            "admin": "主席团",
            "member1": "活动部",
            "member2": "财务部"
        }
    
    # 资金交易（money模块数据）
    if "transactions" not in st.session_state:
        st.session_state.transactions = [
            {"date": "2024-09-01", "amount": 500.0, "desc": "赞助收入", "handler": "admin"},
            {"date": "2024-09-05", "amount": -200.0, "desc": "采购物资", "handler": "member2"}
        ]

# 判断管理员权限
def is_admin():
    return st.session_state.user == "admin"

# 获取用户所属群组
def get_user_group():
    return st.session_state.member_groups.get(st.session_state.user, "未分配")

def main():
    init_session_state()
    
    # 页面配置
    st.set_page_config(
        page_title="学生会管理系统",
        layout="wide"
    )
    
    st.title("🏛️ 学生会管理系统")
    st.divider()
    
    # 侧边栏用户登录
    with st.sidebar:
        st.header("用户登录")
        st.session_state.user = st.text_input("用户名", "admin")
        st.info(f"当前用户：{st.session_state.user}")
        st.info(f"角色：{'管理员' if is_admin() else '成员'}")
        st.caption("© 2024 学生会管理系统")
    
    # 主标签页（对应三个模块）
    tab1, tab2, tab3 = st.tabs(["📅 日历", "👥 群组", "💸 资金"])
    
    with tab1:
        render_calendar(is_admin())  # 调用calendar模块
    
    with tab2:
        render_groups(is_admin(), get_user_group())  # 调用groups模块
    
    with tab3:
        render_money(is_admin())  # 调用money模块

if __name__ == "__main__":
    main()
