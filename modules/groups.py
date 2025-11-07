# modules/groups.py
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
from google_sheet_utils import GoogleSheetHandler

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def render_groups():
    """优化布局紧凑性，减少不必要空白，添加Google Sheets同步功能"""
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.markdown(
        "<p style='line-height: 0.5; font-size: 24px;'>📋 学生事务综合管理系统</p>",
        unsafe_allow_html=True
    )
    st.caption("包含成员管理、收入管理和报销管理三个功能模块")  # 使用caption减小字体和间距
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    group_sheet = None
    try:
        # 从Streamlit Secrets获取认证信息
        if 'google_credentials' in st.secrets:
            sheet_handler = GoogleSheetHandler(credentials=st.secrets['google_credentials'])
            group_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="Group1"
            )
        else:
            st.error("Google Sheets 认证信息未配置，请检查Streamlit Secrets")
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 初始化成员数据并从Google Sheets同步
    if "members" not in st.session_state:
        st.session_state.members = []
    
    # 从Google Sheets同步数据
    if group_sheet and sheet_handler:
        try:
            all_data = group_sheet.get_all_values()
            expected_headers = ["id", "name", "student_id", "created_at"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                group_sheet.clear()
                group_sheet.append_row(expected_headers)
                st.session_state.members = []
            else:
                # 处理数据（跳过表头）
                st.session_state.members = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "student_id": row[2]
                    } 
                    for row in all_data[1:] 
                    if row[0] and row[1] and row[2]  # 确保关键字段不为空
                ]
        except Exception as e:
            st.warning(f"成员数据同步失败: {str(e)}")

    # ---------------------- 1. 成员管理模块 ----------------------
    st.markdown(
        "<p style='line-height: 0.5; font-size: 20px;'>👥 成员管理</p>",
        unsafe_allow_html=True
    )
    st.write("管理成员的基本信息（姓名、学生ID）")
    st.divider()

    # 添加新成员区域（紧凑布局）
    with st.container():  # 使用容器减少外部间距
        st.markdown("<p style='font-size: 16px;'>添加新成员</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("成员姓名*", placeholder="请输入姓名", label_visibility="visible")
        with col2:
            student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID", label_visibility="visible")
        
        # 确认添加按钮紧跟输入框
        if st.button("确认添加", use_container_width=True, key="add_btn"):
            valid = True
            if not name.strip():
                st.error("成员姓名不能为空", icon="❌")
                valid = False
            if not student_id.strip():
                st.error("学生ID不能为空", icon="❌")
                valid = False
            if any(m["student_id"] == student_id for m in st.session_state.members):
                st.error(f"学生ID {student_id} 已存在", icon="❌")
                valid = False

            if valid:
                member_id = f"M{len(st.session_state.members) + 1:03d}"
                new_member = {
                    "id": member_id,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                }
                st.session_state.members.append(new_member)
                
                # 同步到Google Sheets
                if group_sheet and sheet_handler:
                    try:
                        # 添加新记录（包含时间戳）
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        group_sheet.append_row([
                            member_id, 
                            name.strip(), 
                            student_id.strip(),
                            current_time
                        ])
                        st.success(f"成功添加：{name}（ID：{student_id}）", icon="✅")
                    except Exception as e:
                        st.warning(f"同步到Google Sheets失败: {str(e)}")

    st.divider()

    # 成员列表展示
    st.markdown("<p style='font-size: 16px; line-height: 1;'>成员列表</p>", unsafe_allow_html=True)
    if not st.session_state.members:
        st.info("暂无成员信息，请在上方添加", icon="ℹ️")
    else:
        member_df = pd.DataFrame([
            {"序号": i+1, "成员姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ])
        st.dataframe(member_df, use_container_width=True, height=min(300, 50 + len(st.session_state.members)*35))  # 动态调整高度

        # 删除功能（紧凑布局）
        with st.expander("管理成员（删除）", expanded=False):
            for m in st.session_state.members:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_mem_{m['id']}", use_container_width=True):
                        # 从本地删除
                        st.session_state.members = [
                            member for member in st.session_state.members 
                            if member["id"] != m["id"]
                        ]
                        
                        # 同步删除Google Sheets记录
                        if group_sheet and sheet_handler:
                            try:
                                all_rows = group_sheet.get_all_values()
                                for i, row in enumerate(all_rows[1:], start=2):  # 从第2行开始是数据
                                    if row[0] == m["id"]:
                                        group_sheet.delete_rows(i)
                                        st.success(f"已删除：{m['name']}", icon="✅")
                                        st.rerun()
                            except Exception as e:
                                st.warning(f"从Google Sheets删除失败: {str(e)}")

    # 模块间分隔（减少空白）
    st.markdown("---")

    # ---------------------- 2. 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    st.divider()
    st.info("收入管理模块区域 - 后续功能将在此处开发", icon="ℹ️")

    # 模块间分隔
    st.markdown("---")

    # ---------------------- 3. 报销管理模块 ----------------------
    st.header("🧾 报销管理")
    st.write("此模块用于管理各项报销申请及审批流程")
    st.divider()
    st.info("报销管理模块区域 - 后续功能将在此处开发", icon="ℹ️")
