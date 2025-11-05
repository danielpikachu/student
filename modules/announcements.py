# modules/announcements.py
import streamlit as st

def render_announcements():
    """渲染公告模块界面，使用命名空间隔离key"""
    ns = "announcements"  # 命名空间前缀
    
    # 1. 模块标题
    st.subheader("📢 Announcements")
    st.markdown("---")  # 分隔线，优化视觉

    # 2. 检查会话状态中的公告数据（若不存在则初始化）
    if f"{ns}_data" not in st.session_state:
        st.session_state[f"{ns}_data"] = []  # 存储公告列表，每个公告是字典

    # 3. 展示公告列表
    st.write("### Current Announcements")
    if not st.session_state[f"{ns}_data"]:  # 无公告时提示
        st.info("No announcements yet. Check back later!")
    else:  # 有公告时按时间倒序展示（最新在前）
        for idx, announcement in enumerate(reversed(st.session_state[f"{ns}_data"])):
            st.markdown(f"""
            **Announcement {len(st.session_state[f"{ns}_data"]) - idx}**  
            *Date: {announcement['date']}*  
            {announcement['content']}  
            """)
            st.markdown("---")  # 分隔不同公告

    # 4. 管理员专属：添加新公告（通过密码验证模拟管理员权限）
    st.write("### Admin Operations")
    admin_password = st.text_input(
        "Enter Admin Password", 
        type="password",
        key=f"{ns}_admin_pwd"  # 层级化key
    )
    
    # 假设管理员密码为 "sc_admin_2025"
    if admin_password == "sc_admin_2025":
        st.success("Admin authenticated successfully!")
        # 新公告输入表单
        with st.form(key=f"{ns}_new_form"):  # 表单key
            announcement_date = st.date_input(
                "Announcement Date",
                key=f"{ns}_date_input"  # 日期输入key
            )
            announcement_content = st.text_area(
                "Announcement Content", 
                height=150,
                key=f"{ns}_content_area"  # 文本区域key
            )
            submit_btn = st.form_submit_button(
                label="Add New Announcement",
                key=f"{ns}_submit_btn"  # 提交按钮key
            )

            # 表单提交逻辑
            if submit_btn and announcement_content.strip():
                new_announcement = {
                    "date": announcement_date.strftime("%Y-%m-%d"),
                    "content": announcement_content.strip()
                }
                st.session_state[f"{ns}_data"].append(new_announcement)
                st.success("New announcement added successfully!")
            elif submit_btn:
                st.error("Announcement content cannot be empty!")
    elif admin_password != "":
        st.error("Incorrect admin password. Please try again.")
