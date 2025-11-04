import streamlit as st
import pandas as pd
from streamlit_elements import elements, mui  # 需要安装：pip install streamlit-elements

def render_attendance():
    st.set_page_config(layout="wide")
    
    # 初始化状态
    if 'members' not in st.session_state:
        st.session_state.members = []
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
    if 'attendance' not in st.session_state:
        st.session_state.attendance = {}

    # 样式设置
    st.markdown("""
        <style>
            .scrollable-table {
                max-height: 500px;
                overflow-y: auto;
                padding: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.header("Meeting Attendance Records")

    # 核心改进：使用streamlit-elements创建带复选框的表格
    if st.session_state.members and st.session_state.meetings:
        # 准备初始数据
        attendance_data = {}
        for member in st.session_state.members:
            member_id = member["id"]
            attendance_data[member_id] = {
                "name": member["name"],
                **{meeting["id"]: st.session_state.attendance.get((member_id, meeting["id"]), False) 
                  for meeting in st.session_state.meetings}
            }

        # 使用elements创建交互式表格
        with elements("attendance_table"):
            with mui.Paper(elevation=2, sx={"padding": 2}):
                with mui.TableContainer(sx={"maxHeight": 400}):
                    with mui.Table():
                        # 表头
                        with mui.TableHead():
                            with mui.TableRow():
                                mui.TableCell("Member Name")
                                for meeting in st.session_state.meetings:
                                    mui.TableCell(meeting["name"])
                                mui.TableCell("Attendance Rate")

                        # 表体
                        with mui.TableBody():
                            for member in st.session_state.members:
                                member_id = member["id"]
                                attended = sum(
                                    st.session_state.attendance.get((member_id, meeting["id"]), False)
                                    for meeting in st.session_state.meetings
                                )
                                rate = f"{(attended / len(st.session_state.meetings) * 100):.1f}%" if st.session_state.meetings else "N/A"
                                
                                with mui.TableRow():
                                    mui.TableCell(member["name"])
                                    for meeting in st.session_state.meetings:
                                        meeting_id = meeting["id"]
                                        # 复选框组件
                                        def make_callback(m_id, me_id):
                                            def callback(event):
                                                st.session_state.attendance[(m_id, me_id)] = event.target.checked
                                            return callback
                                        
                                        mui.TableCell(
                                            mui.Checkbox(
                                                checked=st.session_state.attendance.get((member_id, meeting_id), False),
                                                onChange=make_callback(member_id, meeting_id),
                                                color="primary"
                                            )
                                        )
                                    mui.TableCell(rate)

    elif not st.session_state.members:
        st.info("No members found. Please import members first.")
    else:
        st.info("No meetings found. Please add meetings first.")

    st.markdown("---")

    # 保持原有管理功能区域不变
    st.header("Attendance Management Tools")

    # 1. 导入成员
    with st.container():
        st.subheader("Import Members")
        if st.button("Import from members.xlsx", key="import_btn"):
            try:
                df = pd.read_excel("members.xlsx")
                first_col = df.columns[0]
                new_members = [str(name).strip() for name in df[first_col].dropna().unique() if str(name).strip()]
                added = 0
                for name in new_members:
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
                st.session_state.meetings.append({
                    "id": len(st.session_state.meetings) + 1, 
                    "name": meeting_name.strip()
                })
                st.success(f"Added meeting: {meeting_name.strip()}")

if __name__ == "__main__":
    render_attendance()
