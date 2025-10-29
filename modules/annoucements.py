# modules/announcements.py
import streamlit as st

def render_announcements():
    """渲染公告模块界面"""
    # 1. 模块标题
    st.subheader("📢 Announcements")
    st.markdown("---")  # 分隔线，优化视觉

    # 2. 检查会话状态中的公告数据（若不存在则初始化）
    if "announcements" not in st.session_state:
        st.session_state.announcements = []  # 存储公告列表，每个公告是字典

    # 3. 展示公告列表
    st.write("### Current Announcements")
    if not st.session_state.announcements:  # 无公告时提示
        st.info("No announcements yet. Check back later!")
    else:  # 有公告时按时间倒序展示（最新在前）
        for idx, announcement in enumerate(reversed(st.session_state.announcements)):
            st.markdown(f"""
            **Announcement {len(st.session_state.announcements) - idx}**  
            *Date: {announcement['date']}*  
            {announcement['content']}  
            """)
            st.markdown("---")  # 分隔不同公告

    # 4. 管理员专属：添加新公告（通过密码验证模拟管理员权限）
    st.write("### Admin Operations")
    admin_password = st.text_input("Enter Admin Password", type="password")
    # 假设管理员密码为 "sc_admin_2025"（实际项目需替换为安全的权限验证逻辑）
    if admin_password == "sc_admin_2025":
        st.success("Admin authenticated successfully!")
        # 新公告输入表单
        with st.form(key="new_announcement_form"):
            announcement_date = st.date_input("Announcement Date")  # 公告日期
            announcement_content = st.text_area("Announcement Content", height=150)  # 公告内容
            submit_btn = st.form_submit_button(label="Add New Announcement")

            # 表单提交逻辑：添加公告到会话状态
            if submit_btn and announcement_content.strip():  # 内容非空才提交
                new_announcement = {
                    "date": announcement_date.strftime("%Y-%m-%d"),  # 日期格式化
                    "content": announcement_content.strip()
                }
                st.session_state.announcements.append(new_announcement)
                st.success("New announcement added successfully!")
            elif submit_btn:  # 内容为空时提示
                st.error("Announcement content cannot be empty!")
    elif admin_password != "":  # 密码输入错误（非空）
        st.error("Incorrect admin password. Please try again.")
