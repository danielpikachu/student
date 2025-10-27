import streamlit as st
# 导入模块（确保模块文件名正确：calendar.py、groups.py、money.py）
from modules.calendar import render_calendar
from modules.groups import render_groups
from modules.money import render_money

# 【简化初始化逻辑】只保留最基础的会话状态，移除复杂数据
def init_session_state():
    # 用户角色（管理员/成员）
    if "user_role" not in st.session_state:
        st.session_state.user_role = "member"  # 默认普通成员
    
    # 日历事件（清空示例数据，避免初始化时加载过多内容）
    if "calendar_events" not in st.session_state:
        st.session_state.calendar_events = {}  # 空字典
    
    # 群组数据（简化为空白列表）
    if "groups" not in st.session_state:
        st.session_state.groups = []  # 空列表
    
    # 成员-群组关联（简化为空白字典）
    if "member_groups" not in st.session_state:
        st.session_state.member_groups = {}  # 空字典
    
    # 资金交易记录（简化为空白列表）
    if "transactions" not in st.session_state:
        st.session_state.transactions = []  # 空列表

# 判断是否为管理员（仅用户名为 "admin" 时有权限）
def is_admin():
    return st.session_state.user == "admin"

# 获取当前用户所属群组（简化逻辑）
def get_user_group():
    return st.session_state.member_groups.get(st.session_state.user, "未分配")

def main():
    # 初始化基础会话状态（无复杂数据）
    init_session_state()
    
    # 页面基础配置（简化布局）
    st.set_page_config(
        page_title="学生会管理系统",
        layout="centered"  # 改用紧凑布局，减少启动资源占用
    )
    
    # 仅显示基础标题和说明
    st.title("🏛️ 学生会管理系统")
    st.write("简化版应用 - 用于测试部署")
    st.divider()
    
    # 侧边栏：仅保留必要的用户输入
    with st.sidebar:
        st.header("用户登录")
        # 仅保留用户名输入，移除多余信息
        st.session_state.user = st.text_input("输入用户名", "admin")  # 默认管理员账号
        st.info(f"角色：{'管理员' if is_admin() else '成员'}")
    
    # 主标签页：调用三个模块（保持结构，但模块内数据已简化）
    tab1, tab2, tab3 = st.tabs(["📅 日历", "👥 群组", "💸 资金"])
    
    with tab1:
        render_calendar(is_admin())  # 调用日历模块
    
    with tab2:
        render_groups(is_admin(), get_user_group())  # 调用群组模块
    
    with tab3:
        render_money(is_admin())  # 调用资金模块

if __name__ == "__main__":
    main()
