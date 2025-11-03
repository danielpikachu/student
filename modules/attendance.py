import streamlit as st
import pandas as pd
import os

def attendance_module():
    st.title("Attendance")
    
    # 分两部分布局：上部分表格，下部分管理工具
    col1, col2 = st.columns([3, 2])  # 调整列宽比例，适配内容
    
    with col1:
        st.header("Meeting Attendance Records")
        
        # 加载成员名单（从members.xlsx导入）
        @st.cache_data
        def load_members():
            file_path = os.path.join(os.path.dirname(__file__), "members.xlsx")
            if os.path.exists(file_path):
                df_members = pd.read_excel(file_path)
                df_members.columns = ["Member Name"]  # 统一列名
                return df_members
            else:
                st.error("members.xlsx 文件不存在，请先准备该文件！")
                return pd.DataFrame(columns=["Member Name"])
        
        df_members = load_members()
        if df_members.empty:
            st.stop()  # 无成员时停止后续渲染
        
        # 初始化会议出勤记录（若未在session_state中）
        if "attendance_records" not in st.session_state:
            st.session_state.attendance_records = df_members.copy()
            # 初始会议列（示例，可根据实际需求调整）
            initial_meetings = ["First Semester Meeting", "Event Planning Session", "Meeting 3", "Meeting 4"]
            for meeting in initial_meetings:
                st.session_state.attendance_records[meeting] = False  # 初始为未出勤
        
        # 计算出勤率：每一行的出勤次数 / 会议总数
        meeting_cols = [col for col in st.session_state.attendance_records.columns if col not in ["Member Name"]]
        if meeting_cols:
            st.session_state.attendance_records["Attendance Rates"] = (
                st.session_state.attendance_records[meeting_cols].sum(axis=1) / len(meeting_cols)
            ).apply(lambda x: f"{x*100:.2f}%")
        else:
            st.session_state.attendance_records["Attendance Rates"] = "0.00%"
        
        # 显示出勤表格
        st.dataframe(st.session_state.attendance_records, use_container_width=True)
    
    with col2:
        st.header("Attendance Management Tools")
        
        # 1. Import members 功能
        if st.button("Import members"):
            df_members = load_members()
            if not df_members.empty:
                st.session_state.attendance_records = df_members.copy()
                st.success("成员名单导入成功！")
        
        # 2. Add Meeting 功能
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Meeting Name")
        if st.button("Add Meeting"):
            if meeting_name and meeting_name not in st.session_state.attendance_records.columns:
                st.session_state.attendance_records[meeting_name] = False
                st.success(f"会议 '{meeting_name}' 添加成功！")
            elif not meeting_name:
                st.warning("请输入会议名称！")
            else:
                st.warning("该会议名称已存在！")

# 若直接运行该模块，用于测试
if __name__ == "__main__":
    attendance_module()
