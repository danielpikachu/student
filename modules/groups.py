# modules/groups.py
import streamlit as st
import pandas as pd
import uuid
import sys
import os
from datetime import datetime

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from google_sheet_utils import GoogleSheetHandler

# 定义允许的访问码与对应组名
ACCESS_CODES = {
    "GROUP001": "第一组",
    "GROUP002": "第二组",
    "GROUP003": "第三组",
    "GROUP004": "第四组",
    "GROUP005": "第五组",
    "GROUP006": "第六组",
    "GROUP007": "第七组",
    "GROUP008": "第八组"
}

def render_groups():
    st.set_page_config(page_title="学生事务管理", layout="wide")
    
    # 初始化会话状态
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_access_code" not in st.session_state:
        st.session_state.current_access_code = None

    # 登录界面
    if not st.session_state.logged_in:
        st.markdown(
            "<p style='line-height: 0.5; font-size: 24px;'>📋 学生事务综合管理系统</p>",
            unsafe_allow_html=True
        )
        st.caption("请输入访问码进入对应组别管理")
        st.divider()
        
        access_code = st.text_input("访问码", placeholder="输入组访问码", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("登录", use_container_width=True):
                if access_code in ACCESS_CODES:
                    st.session_state.logged_in = True
                    st.session_state.current_group = ACCESS_CODES[access_code]
                    st.session_state.current_access_code = access_code
                    st.success(f"登录成功，欢迎进入 {ACCESS_CODES[access_code]}")
                    st.rerun()
                else:
                    st.error("无效的访问码，请重新输入")
        with col2:
            if st.button("清除", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.current_group = None
                st.session_state.current_access_code = None
                st.rerun()
        return

    # 已登录状态 - 显示组名
    st.markdown(
        f"<p style='line-height: 0.5; font-size: 24px;'>📋 学生事务综合管理系统 - {st.session_state.current_group}</p>",
        unsafe_allow_html=True
    )
    st.caption("包含成员管理、收入管理和报销管理三个功能模块")
    st.divider()

    # 登出按钮
    if st.button("切换组别", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_group = None
        st.session_state.current_access_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.rerun()

    # 初始化Google Sheets连接
    sheet_handler = None
    main_sheet = None  # 主表格包含所有组的数据
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")
        # 所有组数据存放在同一个工作表
        main_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="AllGroupsData"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步当前组的成员数据
    current_group_code = st.session_state.current_access_code
    if main_sheet and sheet_handler and (not st.session_state.get("members")):
        try:
            all_data = main_sheet.get_all_values()
            # 主表包含组标识列
            expected_headers = ["group_code", "data_type", "uuid", "id", "name", "student_id", "date", "amount", "description", "created_at"]
            
            if not all_data or all_data[0] != expected_headers:
                main_sheet.clear()
                main_sheet.append_row(expected_headers)
                st.session_state.members = []
            else:
                # 筛选当前组的成员数据
                st.session_state.members = [
                    {
                        "uuid": row[2],
                        "id": row[3],
                        "name": row[4],
                        "student_id": row[5]
                    } 
                    for row in all_data[1:] 
                    if row[0] == current_group_code and row[1] == "member" and row[2]
                ]
        except Exception as e:
            st.warning(f"成员数据同步失败: {str(e)}")

    # 从Google Sheets同步当前组的收入数据
    if main_sheet and sheet_handler and (not st.session_state.get("incomes")):
        try:
            all_data = main_sheet.get_all_values()
            expected_headers = ["group_code", "data_type", "uuid", "id", "name", "student_id", "date", "amount", "description", "created_at"]
            
            if not all_data or all_data[0] != expected_headers:
                # 表头已在成员同步部分处理，这里不再重复处理
                st.session_state.incomes = []
            else:
                # 筛选当前组的收入数据
                st.session_state.incomes = [
                    {
                        "uuid": row[2],
                        "date": row[6],
                        "amount": row[7],
                        "description": row[8]
                    } 
                    for row in all_data[1:] 
                    if row[0] == current_group_code and row[1] == "income" and row[2]
                ]
        except Exception as e:
            st.warning(f"收入数据同步失败: {str(e)}")

    # 初始化本地状态
    if "members" not in st.session_state:
        st.session_state.members = []
    if "incomes" not in st.session_state:
        st.session_state.incomes = []

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
                member_uuid = str(uuid.uuid4())
                # 生成组内唯一ID
                member_id = f"{current_group_code[5:]}_{len(st.session_state.members) + 1:03d}"
                new_member = {
                    "uuid": member_uuid,
                    "id": member_id,
                    "name": name.strip(),
                    "student_id": student_id.strip()
                }
                
                st.session_state.members.append(new_member)
                
                if main_sheet and sheet_handler:
                    try:
                        # 插入带组标识和数据类型的记录
                        main_sheet.append_row([
                            current_group_code,  # 组标识
                            "member",  # 数据类型
                            member_uuid,
                            member_id,
                            name.strip(),
                            student_id.strip(),
                            "",  # 空日期（成员数据用不到）
                            "",  # 空金额（成员数据用不到）
                            "",  # 空描述（成员数据用不到）
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

        # 删除功能
        with st.expander("管理成员（删除）", expanded=False):
            for idx, m in enumerate(st.session_state.members):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{m['name']}（学生ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_mem_{m['uuid']}", use_container_width=True):
                        # 删除本地数据
                        st.session_state.members.pop(idx)
                        
                        # 同步删除Google Sheets数据
                        if main_sheet and sheet_handler:
                            try:
                                # 查找特定组和UUID的记录
                                cell = main_sheet.find(m["uuid"])
                                if cell and main_sheet.row_values(cell.row)[0] == current_group_code:
                                    main_sheet.delete_rows(cell.row)
                                st.success(f"成员 {m['name']} 删除成功！")
                                st.rerun()  # 重新加载页面确保UI更新
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")

    st.markdown("---")

    # ---------------------- 收入管理模块 ----------------------
    st.header("💰 收入管理")
    st.write("此模块用于记录和管理各项收入信息")
    st.divider()

    # 添加新收入区域
    with st.container():
        st.markdown("<p style='font-size: 16px;'>添加新收入</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            income_date = st.date_input("日期*", value=datetime.now(), label_visibility="visible")
        with col2:
            income_amount = st.number_input("金额*", min_value=0.01, step=0.01, format="%.2f", label_visibility="visible")
        with col3:
            income_desc = st.text_input("描述*", placeholder="请输入收入描述", label_visibility="visible")
        
        if st.button("确认添加收入", use_container_width=True, key="add_income_btn"):
            valid = True
            if not income_desc.strip():
                st.error("收入描述不能为空", icon="❌")
                valid = False

            if valid:
                income_uuid = str(uuid.uuid4())
                new_income = {
                    "uuid": income_uuid,
                    "date": income_date.strftime("%Y-%m-%d"),
                    "amount": f"{income_amount:.2f}",
                    "description": income_desc.strip()
                }
                
                st.session_state.incomes.append(new_income)
                
                if main_sheet and sheet_handler:
                    try:
                        # 插入带组标识和数据类型的记录
                        main_sheet.append_row([
                            current_group_code,  # 组标识
                            "income",  # 数据类型
                            income_uuid,
                            "",  # 空ID（收入数据用不到）
                            "",  # 空姓名（收入数据用不到）
                            "",  # 空学生ID（收入数据用不到）
                            new_income["date"],
                            new_income["amount"],
                            new_income["description"],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ])
                        st.success(f"成功添加收入：{income_amount:.2f}元", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"收入同步到Google Sheets失败: {str(e)}")

    st.divider()

    # 收入列表展示
    st.markdown("<p style='font-size: 16px; line-height: 1;'>收入列表</p>", unsafe_allow_html=True)
    if not st.session_state.incomes:
        st.info("暂无收入信息，请在上方添加", icon="ℹ️")
    else:
        # 创建收入数据框
        income_df = pd.DataFrame([
            {"序号": i+1, "日期": m["date"], "金额(元)": m["amount"], "描述": m["description"]}
            for i, m in enumerate(st.session_state.incomes)
        ])
        st.dataframe(income_df, use_container_width=True, height=min(300, 50 + len(st.session_state.incomes)*35))

        # 收入删除功能
        with st.expander("管理收入（删除）", expanded=False):
            for idx, income in enumerate(st.session_state.incomes):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"{income['date']} - {income['amount']}元：{income['description']}")
                with col2:
                    if st.button("删除", key=f"del_income_{income['uuid']}", use_container_width=True):
                        # 删除本地数据
                        st.session_state.incomes.pop(idx)
                        
                        # 同步删除Google Sheets数据
                        if main_sheet and sheet_handler:
                            try:
                                cell = main_sheet.find(income["uuid"])
                                if cell and main_sheet.row_values(cell.row)[0] == current_group_code:
                                    main_sheet.delete_rows(cell.row)
                                st.success("收入记录删除成功！")
                                st.rerun()  # 立即刷新页面，确保UI同步
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")

    st.markdown("---")

    # ---------------------- 报销管理模块 ----------------------
    st.header("🧾 报销管理")
    st.write("此模块用于管理各项报销申请及审批流程")
    st.divider()
    st.info("报销管理模块区域 - 后续功能将在此处开发", icon="ℹ️")
