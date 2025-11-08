# ---------------------- 权限控制装饰器 ----------------------
def require_login(func):
    """登录校验装饰器：未登录则跳转至登录界面"""
    def wrapper(*args, **kwargs):
        if not st.session_state.auth_logged_in:
            st.error("请先登录后再操作！")
            show_login_register_form()
            return
        # 直接传递所有参数给下一个装饰器
        return func(*args, **kwargs)
    return wrapper

def require_edit_permission(func):
    """编辑权限校验装饰器：控制非Groups模块的编辑权限"""
    def wrapper(*args, **kwargs):
        # 设置是否可编辑的标志
        is_editable = st.session_state.auth_is_admin
        # 将权限标志通过kwargs传递给被装饰的函数
        return func(*args, **kwargs, is_editable=is_editable)
    return wrapper

def require_group_edit_permission(func):
    """Group模块编辑权限校验装饰器：控制Group模块的编辑权限"""
    def wrapper(*args, **kwargs):
        is_editable = False
        if st.session_state.auth_is_admin:
            # 管理员直接拥有所有Group编辑权限
            is_editable = True
        else:
            # 普通用户需要输入Access Code
            with st.sidebar.expander("🔑 Group访问验证", expanded=True):
                access_code = st.text_input("请输入Group访问码", type="password")
                if st.button("验证访问权限"):
                    if access_code:  # 实际场景可添加Access Code有效性校验逻辑
                        st.session_state.auth_current_group_code = access_code
                        st.success("访问验证通过，可编辑当前Group！")
                        is_editable = True
                    else:
                        st.error("请输入有效的访问码！")
        # 传递编辑权限状态给模块
        return func(*args, **kwargs, is_editable=is_editable)
    return wrapper

# ---------------------- 页面主逻辑（功能模块渲染部分） ----------------------
# 功能选项卡（6大模块）
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Calendar",
    "📢 Announcements",
    "💰 Financial Planning",
    "📋 Attendance",
    "💸 Money Transfers",
    "👥 Groups"
])

# 修复装饰器顺序，确保参数正确传递
with tab1:
    # 先检查权限再检查登录（装饰器执行顺序是从下到上）
    @require_edit_permission
    @require_login
    def render_calendar_wrapper(is_editable):
        render_calendar(is_editable=is_editable)
    render_calendar_wrapper()

with tab2:
    @require_edit_permission
    @require_login
    def render_announcements_wrapper(is_editable):
        render_announcements(is_editable=is_editable)
    render_announcements_wrapper()

with tab3:
    @require_edit_permission
    @require_login
    def render_financial_wrapper(is_editable):
        render_financial_planning(is_editable=is_editable)
    render_financial_wrapper()

with tab4:
    @require_edit_permission
    @require_login
    def render_attendance_wrapper(is_editable):
        render_attendance(is_editable=is_editable)
    render_attendance_wrapper()

with tab5:
    @require_edit_permission
    @require_login
    def render_transfers_wrapper(is_editable):
        render_money_transfers(is_editable=is_editable)
    render_transfers_wrapper()

with tab6:
    @require_group_edit_permission
    @require_login
    def render_groups_wrapper(is_editable):
        render_groups(is_editable=is_editable)
    render_groups_wrapper()
