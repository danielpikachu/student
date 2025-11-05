# modules/announcements.py
import streamlit as st
from datetime import datetime

def render_announcements():
    """渲染公告模块界面（ann_前缀命名空间）"""
    # 1. 模块标题
    st.subheader("📢 Announcements")
    st.markdown("---")  # 分隔线，优化视觉

    # 2. 展示公告列表
    st.write("### Current Announcements")
    if not st.session_state.ann_list:  # 无公告时提示
        st.info("No announcements yet. Check back later!")
    else:  # 有公告时按时间倒序展示（最新在前）
        for idx, announcement in enumerate(reversed(st.session_state.ann_list)):
            st.markdown(f"""
            **Announcement {len(st.session_state.ann_list) - idx}**  
            *Date: {announcement['date']}*  
            {announcement['content']}  
            """)
            st.markdown("---")  # 分隔不同公告

    # 3. 管理员专属：添加新公告（使用统一系统密码）
    st.write("### Admin Operations")
    admin_password = st.text_input(
        "Enter Admin Password", 
        type="password",
        key="ann_input_admin_pwd"  # 层级化Key：ann_模块_输入组件_密码输入
    )

    if admin_password == st.session_state.sys_admin_password:
        st.success("Admin authenticated successfully!")
        # 新公告输入表单（表单Key唯一）
        with st.form(key="ann_form_new_announcement"):
            announcement_date = st.date_input(
                "Announcement Date",
                key="ann_input_date"  # 层级化Key：ann_模块_输入组件_日期
            )
            announcement_content = st.text_area(
                "Announcement Content", 
                height=150,
                key="ann_input_content"  # 层级化Key：ann_模块_输入组件_内容
            )
            submit_btn = st.form_submit_button(
                label="Add New Announcement",
                key="ann_btn_submit"  # 层级化Key：ann_模块_按钮_提交
            )

            # 表单提交逻辑
            if submit_btn:
                if announcement_content.strip():
                    new_announcement = {
                        "date": announcement_date.strftime("%Y-%m-%d"),
                        "content": announcement_content.strip(),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.ann_list.append(new_announcement)
                    st.success("New announcement added successfully!")
                else:
                    st.error("Announcement content cannot be empty!")
    elif admin_password != "":  # 密码输入错误（非空）
        st.error("Incorrect admin password. Please try again.")
