import streamlit as st
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money import render_money_transfer

# 初始化会话状态（首次运行时设置默认数据）
def init_session_state():
    # 用户角色（管理员/普通成员）
    if "user_role" not in st.session_state:
        st.session_state.user_role = "member"  # 默认普通成员
    
    # 日历事件存储（格式: {"2024-06-01": "活动描述"}）
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {
            "2024-09-15": "迎新大会",
            "2024-10-01": "国庆活动"
        }
    
    # 群组数据
    if "groups" not in st.session_state:
        st.session_state.groups = ["主席团", "活动部", "财务部", "宣传部"]
    
    # 成员-群组关联
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {
            "张三": "主席团",    # 管理员
            "李四": "活动部",
            "王五": "财务部"
        }
    
    # 资金交易记录
    if "transactions" not in st.session_state:
        st.session_state.transactions = [
            {"date": "2024-09-01", "amount": 500.0, "desc": "赞助收入", "handler": "张三"},
            {"date": "2024-09-05", "amount": -200.0, "desc": "采购物资", "handler": "王五"}
        ]

# 判断是否为管理员（仅"张三"是管理员）
def is_admin():
    return st.session_state.user == "张三"

# 获取当前用户所属群组
def get_user_group():
    return st.session_state.member_groups.get(st.session_state.user, "未分配")

def main():
    # 初始化数据
    init_session_state()
    
    # 页面配置
    st.set_page_config(
        page_title="学生会管理系统",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 标题
    st.title("🏛️ 学生会管理系统")
    st.divider()
    
    # 侧边栏：用户登录
    with st.sidebar:
        st.header("用户登录")
        st.session_state.user = st.text_input("输入姓名", "张三")  # 默认管理员账号
        st.info(f"当前用户：{st.session_state.user}")
        st.info(f"用户角色：{'管理员' if is_admin() else '普通成员'}")
        st.divider()
        st.caption("© 2024 学生会管理系统")
    
    # 主标签页：调用三个模块
    tab1, tab2, tab3 = st.tabs(["📅 活动日历", "👥 群组管理", "💸 资金管理"])
    
    with tab1:
        render_calendar(is_admin())
    
    with tab2:
        render_groups(is_admin(), get_user_group())
    
    with tab3:
        render_money_transfer(is_admin())

if __name__ == "__main__":
    main()
