import streamlit as st
import pandas as pd

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []  # 存储成员信息，包含id和name
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []  # 存储会议信息，包含id和name
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}  # {(member_id, meeting_id): bool} 存储考勤状态

    # ---------------------- 上部分：带滚动条的表格 + 打勾功能 ----------------------
    st.header("Meeting Attendance Records")

    # 滚动容器样式（同时支持水平和垂直滚动）
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 240px;  /* 垂直滚动触发高度 */
                overflow-y: auto;  /* 垂直滚动 */
                overflow-x: auto;  /* 水平滚动 */
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            .scrollable-table::-webkit-scrollbar {
                width: 8px;  /* 垂直滚动条宽度 */
                height: 8px; /* 水平滚动条高度 */
            }
            .scrollable-table::-webkit-scrollbar-thumb {
                background: #ccc;
                border-radius: 4px;
            }
            .stCheckbox {margin: 0 !important; padding: 0 !important;}
            .scrollable-table table {
                border-collapse: collapse;
                width: 100%;
                table-layout: fixed; /* 强制列宽均匀分配，解决对齐问题 */
            }
            .scrollable-table th,
            .scrollable-table td {
                border: 1px solid #ddd !important; /* 强制显示边框 */
                padding: 8px 12px;
                text-align: left; /* 统一左对齐 */
                word-wrap: break-word; /* 内容过长时自动换行 */
            }
            /* 解决可能的样式覆盖问题 */
            .scrollable-table * {
                box-sizing: border-box;
            }
        </style>
    """, unsafe_allow_html=True)

    # 带滚动条的表格容器
    with st.markdown('<div class="scrollable-table">', unsafe_allow_html=True):
        # 只有当有成员时才显示表格
        if st.session_state.members:
            # 计算列数：成员名列 + 会议列 + 考勤率列
            col_count = len(st.session_state.meetings) + 2
            # 列宽分配：成员名3份，每个会议1份，考勤率2份
            cols = st.columns([3] + [1]*(col_count-2) + [2])
            
            # 表头
            cols[0].write("**Member Name**")
            # 会议列标题
            for i, meeting in enumerate(st.session_state.meetings):
                cols[i+1].write(f"**{meeting['name']}**")
            # 考勤率列标题
            cols[-1].write("**Attendance Rates**")
            
            # 表格内容（逐行渲染成员）
            for member in st.session_state.members:
                # 成员名
                cols[0].write(member["name"])
                
                # 会议勾选框（每个会议对应一列）
                for i, meeting in enumerate(st.session_state.meetings):
                    with cols[i+1]:
                        # 从状态中获取当前考勤状态，默认为未勾选
                        checked = st.session_state.attendance.get((member["id"], meeting["id"]), False)
                        # 渲染勾选框
                        new_checked = st.checkbox(
                            "",
                            value=checked,
                            key=f"c_{member['id']}_{meeting['id']}",
                            label_visibility="collapsed"
                        )
                        # 更新考勤状态
                        st.session_state.attendance[(member["id"], meeting["id"])] = new_checked
                
                # 计算并显示考勤率
                total_meetings = len(st.session_state.meetings)
                if total_meetings == 0:
                    rate = "N/A"  # 没有会议时显示N/A
                else:
                    attended = sum(1 for m in st.session_state.meetings 
                                  if st.session_state.attendance.get((member["id"], m["id"]), False))
                    rate = f"{(attended / total_meetings * 100):.1f}%"
                cols[-1].write(rate)
        else:
            # 没有成员时显示提示信息
            st.write("No members found. Please import members first.")

    st.markdown('</div>', unsafe_allow_html=True)  # 关闭滚动容器

    # 分隔线
    st.markdown("---")

    # ---------------------- 下部分：管理功能 ----------------------
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="import_btn"):
            try:
                df = pd.read_excel("members.xlsx")
                # 取Excel的第一列作为成员名
                first_col = df.columns[0]
                # 提取非空且去重的成员名
                new_members = [str(name).strip() for name in df[first_col].dropna().unique() if str(name).strip()]
                added = 0
                for name in new_members:
                    # 避免重复添加
                    if name not in [m["name"] for m in st.session_state.members]:
                        st.session_state.members.append({
                            "id": len(st.session_state.members) + 1, 
                            "name": name
                        })
                        added += 1
                st.success(f"Imported {added} members from {first_col} column!")
            except FileNotFoundError:
                st.error("File 'members.xlsx' not found!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # 2. 添加会议
    with st.container():
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Meeting name", placeholder="e.g., Team Sync", key="meeting_input")
        if st.button("Add Meeting", key="add_btn"):
            if not meeting_name.strip():
                st.error("Please enter a meeting name!")
            elif any(m["name"] == meeting_name.strip() for m in st.session_state.meetings):
                st.error("This meeting already exists!")
            else:
                # 添加新会议
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1, 
                    "name": meeting_name.strip()
                })
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
