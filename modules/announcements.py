# modules/announcements.py
import streamlit as st
from datetime import datetime

def render_announcements():
    """Render the announcements module interface (using ann_ prefix namespace)"""
    # 1. Module title
    st.subheader("📢 Announcements")
    st.markdown("---")  # Visual separator

    # 2. Display announcements list
    st.write("### Current Announcements")
    if not st.session_state.ann_list:  # Prompt when no announcements exist
        st.info("No announcements yet. Check back later!")
    else:  # Display in reverse chronological order (newest first)
        for idx, announcement in enumerate(reversed(st.session_state.ann_list)):
            st.markdown(f"""
            **Announcement {len(st.session_state.ann_list) - idx}**  
            *Date: {announcement['date']}*  
            {announcement['content']}  
            """)
            st.markdown("---")  # Separator between announcements

    # 3. Determine if user is admin (module-internal access control)
    # Check if admin status exists in session state, default to False if not
    is_admin = st.session_state.get('is_admin', False)

    # 4. Show edit area only to admins
    if is_admin:
        st.write("### Admin Operations")
        admin_password = st.text_input(
            "Enter Admin Password", 
            type="password",
            key="ann_input_admin_pwd"  # Hierarchical key: ann_module_input_component_password
        )

        if admin_password == st.session_state.sys_admin_password:
            st.success("Admin authenticated successfully!")
            # New announcement input form (unique form key)
            with st.form(key="ann_form_new_announcement"):
                announcement_date = st.date_input(
                    "Announcement Date",
                    key="ann_input_date"  # Hierarchical key: ann_module_input_component_date
                )
                announcement_content = st.text_area(
                    "Announcement Content", 
                    height=150,
                    key="ann_input_content"  # Hierarchical key: ann_module_input_component_content
                )
                submit_btn = st.form_submit_button(
                    label="Add New Announcement",
                    key="ann_btn_submit"  # Hierarchical key: ann_module_button_submit
                )

                # Form submission logic
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
        elif admin_password != "":  # Incorrect password (non-empty input)
            st.error("Incorrect admin password. Please try again.")
