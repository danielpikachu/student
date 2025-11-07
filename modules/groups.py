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

# 定义允许的访问码与对应组名（8个组）
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
    
    # 初始化会话状态（记录登录状态、当前组信息）
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_group" not in st.session_state:
        st.session_state.current_group = None
    if "current_group_code" not in st.session_state:  # 存储当前组的访问码（如GROUP001）
        st.session_state.current_group_code = None
    # 初始化数据存储（成员、收入、报销）
    for key in ["members", "incomes", "expenses"]:
        if key not in st.session_state:
            st.session_state[key] = []

    # 登录界面
    if not st.session_state.logged_in:
        st.markdown("<h2>📋 学生事务综合管理系统</h2>", unsafe_allow_html=True)
        st.caption("请输入访问码进入对应组别管理")
        st.divider()
        
        access_code = st.text_input("访问码", placeholder="例如：GROUP001", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("登录", use_container_width=True):
                if access_code in ACCESS_CODES:
                    st.session_state.logged_in = True
                    st.session_state.current_group = ACCESS_CODES[access_code]
                    st.session_state.current_group_code = access_code
                    st.success(f"登录成功，欢迎进入 {ACCESS_CODES[access_code]}")
                    st.rerun()
                else:
                    st.error("无效的访问码，请重新输入")
        with col2:
            if st.button("清除", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.current_group = None
                st.session_state.current_group_code = None
                st.rerun()
        return

    # 已登录状态 - 显示组名
    st.markdown(f"<h2>📋 学生事务综合管理系统 - {st.session_state.current_group}</h2>", unsafe_allow_html=True)
    st.caption("包含成员管理、收入管理和报销管理三个功能模块")
    st.divider()

    # 登出/切换组别按钮
    if st.button("切换组别", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_group = None
        st.session_state.current_group_code = None
        st.session_state.members = []
        st.session_state.incomes = []
        st.session_state.expenses = []
        st.rerun()

    # 初始化Google Sheets连接（单表AllGroupsData，已存在）
    sheet_handler = None
    main_sheet = None
    try:
        sheet_handler = GoogleSheetHandler(credentials_path="")  # 确保credentials配置正确
        # 连接到已存在的Student文件中的AllGroupsData工作表
        main_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",  # 文件名已修正为Student
            worksheet_name="AllGroupsData"  # 已存在的工作表名
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
        return  # 若工作表不存在则直接返回，不继续执行

    # 从单表同步当前组的数据（成员、收入、报销）
    current_code = st.session_state.current_group_code
    if main_sheet and sheet_handler:
        try:
            all_rows = main_sheet.get_all_values()
            if len(all_rows) < 1:
                st.warning("工作表为空，请先确认表头格式是否正确")
                return
            
            # 解析表头，确定字段索引（避免字段顺序变化导致错误）
            header = all_rows[0]
            col_indices = {col: idx for idx, col in enumerate(header)}
            required_cols = ["group_code", "data_type", "uuid", "created_at"]
            if not all(col in col_indices for col in required_cols):
                st.error("工作表表头格式错误，请检查是否包含以下字段：group_code, data_type, uuid, created_at")
                return

            # 筛选当前组的成员数据（data_type=member）
            st.session_state.members = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "name": row[col_indices["name"]],
                    "student_id": row[col_indices["student_id"]]
                }
                for row in all_rows[1:]  # 跳过表头
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "member"
            ]

            # 筛选当前组的收入数据（data_type=income）
            st.session_state.incomes = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]]
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "income"
            ]

            # 筛选当前组的报销数据（data_type=expense）
            st.session_state.expenses = [
                {
                    "uuid": row[col_indices["uuid"]],
                    "date": row[col_indices["date"]],
                    "amount": row[col_indices["amount"]],
                    "description": row[col_indices["description"]]
                }
                for row in all_rows[1:]
                if row[col_indices["group_code"]] == current_code 
                and row[col_indices["data_type"]] == "expense"
            ]

        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # ---------------------- 成员管理模块 ----------------------
    st.subheader("👥 成员管理")
    st.write("管理成员的基本信息（姓名、学生ID）")
    st.divider()

    # 添加新成员
    with st.container():
        st.markdown("**添加新成员**", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("成员姓名*", placeholder="请输入姓名")
        with col2:
            student_id = st.text_input("学生ID*", placeholder="请输入唯一标识ID")
        
        if st.button("确认添加成员", use_container_width=True, key="add_member"):
            if not name or not student_id:
                st.error("姓名和学生ID不能为空")
                return
            if any(m["student_id"] == student_id for m in st.session_state.members):
                st.error(f"学生ID {student_id} 已存在")
                return

            # 生成唯一码
            member_uuid = str(uuid.uuid4())
            new_member = {
                "uuid": member_uuid,
                "name": name.strip(),
                "student_id": student_id.strip()
            }
            st.session_state.members.append(new_member)

            # 写入Google Sheet（单表）
            if main_sheet:
                try:
                    main_sheet.append_row([
                        current_code,  # group_code
                        "member",      # data_type
                        member_uuid,   # uuid
                        name.strip(),  # name
                        student_id.strip(),  # student_id
                        "", "", "",    # 收入/报销字段留空
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # created_at
                    ])
                    st.success(f"成功添加成员：{name}")
                except Exception as e:
                    st.warning(f"同步到表格失败: {str(e)}")

    # 显示成员列表
    st.divider()
    st.markdown("**成员列表**", unsafe_allow_html=True)
    if not st.session_state.members:
        st.info("暂无成员，请添加")
    else:
        member_df = pd.DataFrame([
            {"序号": i+1, "姓名": m["name"], "学生ID": m["student_id"]}
            for i, m in enumerate(st.session_state.members)
        ])
        st.dataframe(member_df, use_container_width=True)

        # 删除成员
        with st.expander("删除成员", expanded=False):
            for m in st.session_state.members:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{m['name']}（ID：{m['student_id']}）")
                with col2:
                    if st.button("删除", key=f"del_member_{m['uuid']}"):
                        # 本地删除
                        st.session_state.members = [x for x in st.session_state.members if x["uuid"] != m["uuid"]]
                        # 表格删除（通过uuid定位）
                        if main_sheet:
                            try:
                                cell = main_sheet.find(m["uuid"])
                                if cell:
                                    row = main_sheet.row_values(cell.row)
                                    # 双重验证：确保是当前组的数据
                                    if row[0] == current_code and row[1] == "member":
                                        main_sheet.delete_rows(cell.row)
                                        st.success(f"已删除 {m['name']}")
                                        st.rerun()
                            except Exception as e:
                                st.warning(f"删除同步失败: {str(e)}")

    # ---------------------- 收入管理模块 ----------------------
    st.subheader("💰 收入管理")
    st.write("记录和管理各项收入信息")
    st.divider()

    # 添加新收入
    with st.container():
        st.markdown("**添加新收入**", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            income_date = st.date_input("日期*", datetime.now())
        with col2:
            income_amount = st.number_input("金额*", min_value=0.01, step=0.01, format="%.2f")
        with col3:
            income_desc = st.text_input("描述*", placeholder="请输入收入来源")
        
        if st.button("确认添加收入", use_container_width=True, key="add_income"):
            if not income_desc:
                st.error("收入描述不能为空")
                return

            income_uuid = str(uuid.uuid4())
            new_income = {
                "uuid": income_uuid,
                "date": income_date.strftime("%Y-%m-%d"),
                "amount": f"{income_amount:.2f}",
                "description": income_desc.strip()
            }
            st.session_state.incomes.append(new_income)

            # 写入Google Sheet
            if main_sheet:
                try:
                    main_sheet.append_row([
                        current_code,
                        "income",
                        income_uuid,
                        "", "",  # 成员字段留空
                        new_income["date"],
                        new_income["amount"],
                        new_income["description"],
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
                    st.success(f"成功添加收入：{income_amount:.2f}元")
                except Exception as e:
                    st.warning(f"同步到表格失败: {str(e)}")

    # 显示收入列表
    st.divider()
    st.markdown("**收入列表**", unsafe_allow_html=True)
    if not st.session_state.incomes:
        st.info("暂无收入，请添加")
    else:
        income_df = pd.DataFrame([
            {"序号": i+1, "日期": m["date"], "金额(元)": m["amount"], "描述": m["description"]}
            for i, m in enumerate(st.session_state.incomes)
        ])
        st.dataframe(income_df, use_container_width=True)

        # 删除收入
        with st.expander("删除收入", expanded=False):
            for income in st.session_state.incomes:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{income['date']} - {income['amount']}元：{income['description']}")
                with col2:
                    if st.button("删除", key=f"del_income_{income['uuid']}"):
                        st.session_state.incomes = [x for x in st.session_state.incomes if x["uuid"] != income["uuid"]]
                        if main_sheet:
                            try:
                                cell = main_sheet.find(income["uuid"])
                                if cell:
                                    row = main_sheet.row_values(cell.row)
                                    if row[0] == current_code and row[1] == "income":
                                        main_sheet.delete_rows(cell.row)
                                        st.success("已删除收入记录")
                                        st.rerun()
                            except Exception as e:
                                st.warning(f"删除同步失败: {str(e)}")

    # ---------------------- 报销管理模块 ----------------------
    st.subheader("🧾 报销管理")
    st.write("记录和管理各项报销信息")
    st.divider()

    # 添加新报销（逻辑同收入，仅data_type不同）
    with st.container():
        st.markdown("**添加新报销**", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            exp_date = st.date_input("报销日期*", datetime.now(), key="exp_date")
        with col2:
            exp_amount = st.number_input("报销金额*", min_value=0.01, step=0.01, format="%.2f", key="exp_amount")
        with col3:
            exp_desc = st.text_input("报销描述*", placeholder="请输入报销事由", key="exp_desc")
        
        if st.button("确认添加报销", use_container_width=True, key="add_expense"):
            if not exp_desc:
                st.error("报销描述不能为空")
                return

            exp_uuid = str(uuid.uuid4())
            new_exp = {
                "uuid": exp_uuid,
                "date": exp_date.strftime("%Y-%m-%d"),
                "amount": f"{exp_amount:.2f}",
                "description": exp_desc.strip()
            }
            st.session_state.expenses.append(new_exp)

            # 写入Google Sheet
            if main_sheet:
                try:
                    main_sheet.append_row([
                        current_code,
                        "expense",  # 数据类型为expense
                        exp_uuid,
                        "", "",  # 成员字段留空
                        new_exp["date"],
                        new_exp["amount"],
                        new_exp["description"],
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
                    st.success(f"成功添加报销：{exp_amount:.2f}元")
                except Exception as e:
                    st.warning(f"同步到表格失败: {str(e)}")

    # 显示报销列表
    st.divider()
    st.markdown("**报销列表**", unsafe_allow_html=True)
    if not st.session_state.expenses:
        st.info("暂无报销记录，请添加")
    else:
        exp_df = pd.DataFrame([
            {"序号": i+1, "日期": m["date"], "金额(元)": m["amount"], "描述": m["description"]}
            for i, m in enumerate(st.session_state.expenses)
        ])
        st.dataframe(exp_df, use_container_width=True)

    st.divider()
