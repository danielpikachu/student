# modules/groups.py
import streamlit as st
import pandas as pd
import uuid  # 新增：导入uuid模块
import sys
import os
from datetime import datetime

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

def render_groups():
    st.set_page_config(page_title="学生事务管理", layout="wide")
    st.markdown(
        "<p style='line-height: 0.5; font-size: 24px;'>📋 学生事务综合管理系统</p>",
        unsafe_allow_html=True
    )
    st.caption("包含成员管理、收入管理和报销管理三个功能模块")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    group_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        group_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="Group1"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据
    if group_sheet and sheet_handler and (not st.session_state.get("members")):
        try:
            all_data = group_sheet.get_all_values()
            expected_headers = ["uuid", "id", "name", "student_id", "created_at"]
            
            if not all_data or all_data[0] != expected_headers:
                group_sheet.clear()
                group_sheet.append_row(expected_headers)
                st.session_state.members = []
            else:
                # 处理数据（包含uuid字段）
                st.session_state.members = [
                    {
                        "uuid": row[0],
                        "id": row[1],
                        "name": row[2],
                        "student_id": row[3]
                    } 
                    for row in all_data[1:] 
                    if row[0]
                ]
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 初始化本地状态（确保包含uuid字段）
    if "members" not in st.session_state:
        st.session_state.members = []

    # ---------------------- 成员管理模块 ----------------------
    st.markdown(
        "<p style='line-height: 0.5; font-size: 20px;'>👥 成员管理</p>",
        unsafe_allow_html=True
    )
    st.write("管理成员的基本信息（姓名、学生ID）")
    st.divider()

    # 添加新成员区域
    with st.container():
        st.markdown("<p style='font-size: 16px;'>添加新成员</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("成员姓名*", placeholder="请输入姓名", label_visibility="visible")
        with col2:
            student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID", label_visibility="visible")
        
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
                # 生成uuid（关键修复：新增uuid字段）
                member_uuid = str(uuid.uuid4())
                member_id = f"M{len(st.session_state.members) + 1:03d}"
                new_member = {
                    "uuid": member_uuid,  # 新增：添加uuid字段
                    "id": member_id,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                }
                
                st.session_state.members.append(new_member)
                
                # 同步到Google Sheets
                if group_sheet and sheet_handler:
                    try:
                        group_sheet.append_row([
                            member_uuid,
                            member_id,
                            name.strip(),
                            student_id.strip(),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        st.success(f"成功添加：{name}（ID：{student_id}）", icon="✅")
                        st.rerun()
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
        st.dataframe(member_df, use_container_width=True, height=min(300, 50 + len(st.session_state.members)*35))

        # 删除功能（现在可以正确访问m['uuid']）
        with st.expander("管理成员（删除）", expanded=False):
            for idx, m in enumerate(st.session_state.members):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_mem_{m['uuid']}", use_container_width=True):
                        st.session_state.members.pop(idx)
                        
                        if group_sheet and sheet_handler:
                            try:
                                cell = group_sheet.find(m["uuid"])
                                if cell:
                                    group_sheet.delete_rows(cell.row)
                                st.success(f"成员 {m['name']} 删除成功！")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")

    st.markdown("---")

    # 收入管理和报销管理模块（保持不变）
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    st.divider()
    st.info("收入管理模块区域 - 后续功能将在此处开发", icon="ℹ️")

    st.markdown("---")

    st.header("🧾 报销管理")
    st.write("此模块用于管理各项报销申请及审批流程")
    st.divider()
    st.info("报销管理模块区域 - 后续功能将在此处开发", icon="ℹ️")
