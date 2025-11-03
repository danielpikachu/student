import streamlit as st
import pandas as pd
import os
from pathlib import Path

def attendance_module():
    st.title("Attendance")
    
    # 分两部分布局：上部分表格，下部分管理工具
    col1, col2 = st.columns([3, 2])  # 调整列宽比例
    
    with col1:
        st.header("Meeting Attendance Records")
        
        # 加载成员名单（members.xlsx在根目录，与main.py同级）
        @st.cache_data
        def load_members():
            # 根目录路径（modules文件夹的上级目录）
            root_dir = Path(__file__).parent.parent
            file_path = root_dir / "members.xlsx"
            
            if os.path.exists(file_path):
                df_members = pd.read_excel(file_path)
                # 确保列名统一为“Member Name”
                df_members.columns = ["Member Name"] if not df_members.empty else ["Member Name"]
                return df_members
            else:
                st.error("根目录下未找到 members.xlsx 文件，请先准备该文件！")
                return pd.DataFrame(columns=["Member Name"])
        
        df_members = load_members()
        if df_members.empty:
            st.stop()  # 无成员时停止后续渲染
        
        # 初始化会议出勤记录（存储在session_state中）
        if "attendance_records" not in st.session_state:
            st.session_state.attendance_records = df_members.copy()
            # 初始示例会议（可根据实际需求调整）
            initial_meetings = ["First Meeting", "Second Meeting", "Third Meeting"]
            for meeting in initial_meetings:
                st.session_state.attendance_records[meeting] = False  # 初始为未出勤
        
        # 计算出勤率：出勤次数 / 总会议数（保留2位小数百分比）
        meeting_cols = [col for col in st.session_state.attendance_records.columns 
                       if col not in ["Member Name", "Attendance Rates"]]
        if meeting_cols:
            st.session_state.attendance_records["Attendance Rates"] = (
                st.session_state.attendance_records[meeting_cols].sum(axis=1) / len(meeting_cols)
            ).apply(lambda x: f"{x*100:.2f}%")
        else:
            st.session_state.attendance_records["Attendance Rates"] = "0.00%"
        
        # 显示出勤表格（支持编辑出勤状态）
        edited_df = st.data_editor(
            st.session_state.attendance_records,
            use_container_width=True,
            column_config={
                "Member Name": st.column_config.TextColumn("Member Name", disabled=True),  # 成员名不可编辑
                "Attendance Rates": st.column_config.TextColumn("Attendance Rates", disabled=True)  # 出勤率自动计算，不可编辑
            },
            disabled=["Member Name", "Attendance Rates"]
        )
        # 更新session_state中的数据
        st.session_state.attendance_records = edited_df
    
    with col2:
        st.header("Attendance Management Tools")
        
        # 1. 导入成员（重新加载members.xlsx）
        if st.button("Import members"):
            df_members = load_members()
            if not df_members.empty:
                # 保留已有的会议列，仅更新成员名单
                existing_meetings = [col for col in st.session_state.attendance_records.columns 
                                    if col not in ["Member Name", "Attendance Rates"]]
                st.session_state.attendance_records = df_members.copy()
                for meeting in existing_meetings:
                    st.session_state.attendance_records[meeting] = False  # 新成员默认未出勤
                st.success("成员名单已从 members.xlsx 导入！")
        
        # 2. 添加会议
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Enter Meeting Name")
        if st.button("Add Meeting"):
            if meeting_name.strip() == "":
                st.warning("请输入会议名称！")
            elif meeting_name in st.session_state.attendance_records.columns:
                st.warning(f"会议 '{meeting_name}' 已存在！")
            else:
                # 新增会议列，默认值为False（未出勤）
                st.session_state.attendance_records[meeting_name] = False
                st.success(f"会议 '{meeting_name}' 已添加！")

# 测试用（直接运行该模块时）
if __name__ == "__main__":
    attendance_module()
