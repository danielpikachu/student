import streamlit as st
import pandas as pd
import os
from pathlib import Path

def attendance_module():
    st.title("Attendance")
    
    # 上下两部分布局
    col1, col2 = st.columns([3, 2])  # 左侧表格区域宽，右侧工具区域窄
    
    with col1:
        st.header("Meeting Attendance Records")
        
        # 加载根目录下的members.xlsx（modules文件夹与main.py平级，根目录即main.py所在目录）
        @st.cache_data
        def load_members():
            # 根目录路径 = modules文件夹的父目录（因attendance.py在modules内）
            root_dir = Path(__file__).resolve().parent.parent  # 等价于：main.py所在目录
            file_path = root_dir / "members.xlsx"  # 拼接成员文件路径
            
            if os.path.exists(file_path):
                df_members = pd.read_excel(file_path)
                # 确保列名统一为“Member Name”（兼容不同表头的Excel）
                if not df_members.empty:
                    df_members.columns = ["Member Name"]
                return df_members
            else:
                st.error("未找到 members.xlsx 文件，请将该文件放在与 main.py 同级的根目录下！")
                return pd.DataFrame(columns=["Member Name"])
        
        # 加载成员数据
        df_members = load_members()
        if df_members.empty:
            st.stop()  # 无成员时停止渲染后续内容
        
        # 初始化出勤记录（存储在session_state中，跨会话保留）
        if "attendance_records" not in st.session_state:
            st.session_state.attendance_records = df_members.copy()
            # 初始示例会议（可根据实际需求删除或修改）
            initial_meetings = ["Kickoff Meeting", "Weekly Sync", "Project Review"]
            for meeting in initial_meetings:
                st.session_state.attendance_records[meeting] = False  # 初始默认未出勤
        
        # 计算出勤率（自动更新）
        # 筛选所有会议列（排除成员名和出勤率本身）
        meeting_cols = [
            col for col in st.session_state.attendance_records.columns 
            if col not in ["Member Name", "Attendance Rates"]
        ]
        if meeting_cols:  # 存在会议时计算
            st.session_state.attendance_records["Attendance Rates"] = (
                st.session_state.attendance_records[meeting_cols].sum(axis=1) / len(meeting_cols)
            ).apply(lambda x: f"{x*100:.2f}%")  # 转为百分比格式
        else:  # 无会议时默认0%
            st.session_state.attendance_records["Attendance Rates"] = "0.00%"
        
        # 显示可编辑的出勤表格
        edited_records = st.data_editor(
            st.session_state.attendance_records,
            use_container_width=True,
            column_config={
                "Member Name": st.column_config.TextColumn(
                    "Member Name", 
                    disabled=True  # 成员名不可编辑
                ),
                "Attendance Rates": st.column_config.TextColumn(
                    "Attendance Rates", 
                    disabled=True  # 出勤率自动计算，不可编辑
                )
            },
            disabled=["Member Name", "Attendance Rates"],  # 锁定不可编辑列
            key="attendance_editor"
        )
        # 更新session_state中的数据（保持编辑后的数据同步）
        st.session_state.attendance_records = edited_records
    
    with col2:
        st.header("Attendance Management Tools")
        
        # 1. 导入成员按钮（重新加载members.xlsx）
        if st.button("Import members", key="import_members"):
            df_members = load_members()
            if not df_members.empty:
                # 保留已有的会议列，仅更新成员列表
                existing_meetings = [
                    col for col in st.session_state.attendance_records.columns 
                    if col not in ["Member Name", "Attendance Rates"]
                ]
                # 重建出勤记录（新成员默认未出勤）
                st.session_state.attendance_records = df_members.copy()
                for meeting in existing_meetings:
                    st.session_state.attendance_records[meeting] = False
                st.success("成员名单已从根目录的 members.xlsx 导入！")
        
        # 2. 添加会议功能
        st.subheader("Add Meeting")
        meeting_name = st.text_input("Enter meeting name", key="meeting_name_input")
        if st.button("Add Meeting", key="add_meeting_btn"):
            if not meeting_name.strip():  # 检查空输入
                st.warning("请输入会议名称！")
            elif meeting_name in st.session_state.attendance_records.columns:  # 检查重复
                st.warning(f"会议 '{meeting_name}' 已存在，请更换名称！")
            else:  # 新增会议列
                st.session_state.attendance_records[meeting_name] = False  # 默认未出勤
                st.success(f"会议 '{meeting_name}' 已添加！")

# 测试入口（直接运行该模块时执行）
if __name__ == "__main__":
    attendance_module()
