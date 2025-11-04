import streamlit as st
import pandas as pd
import uuid

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态（使用uuid确保id唯一）
    if 'members' not in st.session_state:
        st.session_state.members = []  # 格式: [{"id": str, "name": str}, ...]
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 格式: [{"id": str, "name": str}, ...]
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # 格式: {(member_id, meeting_id): bool, ...}

    # 确保样式正确
    st.markdown("""
        <style>
            .checkbox-container {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
            }
            .scrollable {
                max-height: 400px;
                overflow-y: auto;
                padding: 10px;
                border: 1px solid #eee;
                border-radius: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("会议出勤记录表")

    # 1. 成员管理
    with st.expander("成员管理", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_member = st.text_input("添加成员", placeholder="输入成员姓名")
            if st.button("添加") and new_member.strip():
                member_id = str(uuid.uuid4())
                st.session_state.members.append({"id": member_id, "name": new_member.strip()})
                st.success(f"已添加成员: {new_member.strip()}")
        
        with col2:
            st.write("当前成员列表:")
            st.write([m["name"] for m in st.session_state.members] or "暂无成员")

    # 2. 会议管理
    with st.expander("会议管理", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_meeting = st.text_input("添加会议", placeholder="输入会议名称/日期")
            if st.button("创建会议") and new_meeting.strip():
                meeting_id = str(uuid.uuid4())
                st.session_state.meetings.append({"id": meeting_id, "name": new_meeting.strip()})
                st.success(f"已创建会议: {new_meeting.strip()}")
        
        with col2:
            st.write("当前会议列表:")
            st.write([m["name"] for m in st.session_state.meetings] or "暂无会议")

    # 3. 出勤记录表格（核心部分）
    st.subheader("出勤记录")
    with st.container():
        if st.session_state.members and st.session_state.meetings:
            # 创建表格结构
            with st.markdown('<div class="scrollable">', unsafe_allow_html=True):
                # 表头
                header_cols = st.columns(len(st.session_state.meetings) + 2)
                with header_cols[0]:
                    st.write("**成员**")
                for i, meeting in enumerate(st.session_state.meetings):
                    with header_cols[i + 1]:
                        st.write(f"**{meeting['name']}**")
                with header_cols[-1]:
                    st.write("**出勤率**")

                # 表格内容（逐行生成）
                for member in st.session_state.members:
                    row_cols = st.columns(len(st.session_state.meetings) + 2)
                    
                    # 成员姓名
                    with row_cols[0]:
                        st.write(member["name"])
                    
                    # 出勤复选框（核心交互）
                    attended_count = 0
                    for i, meeting in enumerate(st.session_state.meetings):
                        key = f"att_{member['id']}_{meeting['id']}"
                        current_state = st.session_state.attendance.get((member['id'], meeting['id']), False)
                        
                        with row_cols[i + 1]:
                            with st.markdown('<div class="checkbox-container">', unsafe_allow_html=True):
                                # 显示可交互的复选框
                                new_state = st.checkbox(
                                    label="",  # 空标签
                                    value=current_state,
                                    key=key,
                                    label_visibility="collapsed"  # 隐藏标签
                                )
                            # 更新状态
                            st.session_state.attendance[(member['id'], meeting['id'])] = new_state
                            if new_state:
                                attended_count += 1
                    
                    # 计算出勤率
                    total = len(st.session_state.meetings)
                    rate = (attended_count / total * 100) if total > 0 else 0
                    with row_cols[-1]:
                        st.write(f"{rate:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("请先添加成员和会议以生成出勤表格")

if __name__ == "__main__":
    render_attendance()
