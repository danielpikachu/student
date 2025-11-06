# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类（与Calendar模块共用）
from google_sheet_utils import GoogleSheetHandler

def add_custom_css():
    """添加自定义CSS样式"""
    st.markdown("""
    <style>
    .section-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .stExpander {
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def init_google_sheet_handler():
    """初始化Google Sheet处理器（与Calendar模块一致）"""
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        return GoogleSheetHandler(credentials_path=creds_path)
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")
        return None

def get_or_create_worksheet(sheet_handler, group_name):
    """获取或创建指定小组在Student表格中的子工作表"""
    if not sheet_handler:
        return None
    
    try:
        # 尝试获取Student表格中已存在的小组工作表
        return sheet_handler.get_worksheet(
            spreadsheet_name="Student",  # 复用已存在的Student主表格
            worksheet_name=group_name    # 子工作表名为Group1~Group8
        )
    except Exception as e:
        # 子工作表不存在时，在Student表格中创建新的
        try:
            worksheet = sheet_handler.create_worksheet(
                spreadsheet_name="Student",
                worksheet_name=group_name
            )
            
            # 初始化表头结构（三部分数据区域）
            worksheet.append_row(["Members", "", "", ""])
            worksheet.append_row(["Name", "StudentID", "Position", "Contact"])  # 成员表头
            worksheet.append_row(["", "", "", ""])  # 分隔行
            worksheet.append_row(["Earnings", "", "", ""])
            worksheet.append_row(["Date", "Amount", "Description", ""])  # 收入表头
            worksheet.append_row(["", "", "", ""])  # 分隔行
            worksheet.append_row(["Reimbursements", "", "", ""])
            worksheet.append_row(["Date", "Amount", "Description", "Status"])  # 报销表头
            
            return worksheet
        except Exception as e:
            st.error(f"在Student表格中创建{group_name}子工作表失败: {str(e)}")
            return None

def load_group_data(worksheet):
    """从工作表加载小组数据（成员、收入、报销）"""
    if not worksheet:
        return {"members": [], "earnings": [], "reimbursements": []}
    
    try:
        all_data = worksheet.get_all_values()
        data = {"members": [], "earnings": [], "reimbursements": []}
        current_section = None  # 用于标记当前解析的区域
        
        for row in all_data:
            # 识别数据区域的标题行
            if row[0] == "Members":
                current_section = "members"
                continue
            elif row[0] == "Earnings":
                current_section = "earnings"
                continue
            elif row[0] == "Reimbursements":
                current_section = "reimbursements"
                continue
            
            # 跳过空行和表头行
            if not current_section or not row[0] or row[0] in ["Name", "Date"]:
                continue
            
            # 解析不同区域的数据
            if current_section == "members":
                data["members"].append({
                    "Name": row[0],
                    "StudentID": row[1],
                    "Position": row[2],
                    "Contact": row[3]
                })
            elif current_section == "earnings":
                data["earnings"].append({
                    "Date": row[0],
                    "Amount": float(row[1]) if row[1] else 0.0,
                    "Description": row[2]
                })
            elif current_section == "reimbursements":
                data["reimbursements"].append({
                    "Date": row[0],
                    "Amount": float(row[1]) if row[1] else 0.0,
                    "Description": row[2],
                    "Status": row[3] or "Pending"
                })
        
        return data
    except Exception as e:
        st.error(f"加载小组数据失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}

def clear_section_data(worksheet, section_title):
    """清空指定区域的数据（保留标题和表头）"""
    all_data = worksheet.get_all_values()
    start_row = None
    end_row = None
    
    # 找到目标区域的起止行
    for i, row in enumerate(all_data):
        if row[0] == section_title:
            start_row = i + 2  # 标题行+1是表头，再+1是数据起始行
        elif start_row and row[0] in ["Members", "Earnings", "Reimbursements", ""]:
            end_row = i - 1  # 区域结束行
            break
    
    # 如果找到区域且有数据行，删除数据
    if start_row and (end_row is None or end_row >= start_row):
        end_row = end_row if end_row is not None else len(all_data) - 1
        # Google Sheets行索引从1开始，需要+1转换
        worksheet.delete_rows(start_row + 1, end_row - start_row + 1)
    return start_row

def save_members(worksheet, members):
    """保存成员数据到工作表"""
    if not worksheet or not members:
        return False
        
    try:
        # 清空现有成员数据
        start_row = clear_section_data(worksheet, "Members")
        if start_row is None:
            return False
        
        # 插入新成员数据
        for member in members:
            worksheet.insert_row(
                [member["Name"], member["StudentID"], member["Position"], member["Contact"]],
                start_row + 1  # 从数据起始行开始插入
            )
        return True
    except Exception as e:
        st.error(f"保存成员数据失败: {str(e)}")
        return False

def save_earnings(worksheet, earnings):
    """保存收入数据到工作表"""
    if not worksheet or not earnings:
        return False
        
    try:
        start_row = clear_section_data(worksheet, "Earnings")
        if start_row is None:
            return False
        
        for earning in earnings:
            worksheet.insert_row(
                [earning["Date"], earning["Amount"], earning["Description"], ""],
                start_row + 1
            )
        return True
    except Exception as e:
        st.error(f"保存收入数据失败: {str(e)}")
        return False

def save_reimbursements(worksheet, reimbursements):
    """保存报销数据到工作表"""
    if not worksheet or not reimbursements:
        return False
        
    try:
        start_row = clear_section_data(worksheet, "Reimbursements")
        if start_row is None:
            return False
        
        for reimbursement in reimbursements:
            worksheet.insert_row(
                [reimbursement["Date"], reimbursement["Amount"], 
                 reimbursement["Description"], reimbursement["Status"]],
                start_row + 1
            )
        return True
    except Exception as e:
        st.error(f"保存报销数据失败: {str(e)}")
        return False

def render_groups():
    """渲染群组管理界面"""
    add_custom_css()
    st.header("👥 小组管理 (Groups Management)")
    st.write("管理小组成员、收入和报销请求")
    st.divider()

    # 初始化Google Sheets连接（与Calendar模块共用逻辑）
    sheet_handler = init_google_sheet_handler()
    
    # 创建8个小组的选项卡
    group_names = [f"Group{i}" for i in range(1, 9)]
    tabs = st.tabs(group_names)
    
    # 为每个小组渲染界面
    for i, tab in enumerate(tabs):
        group_name = group_names[i]
        with tab:
            # 初始化会话状态（使用唯一key：grp_{group_name}_xxx）
            if f"grp_{group_name}_data" not in st.session_state:
                st.session_state[f"grp_{group_name}_data"] = {
                    "members": [],
                    "earnings": [],
                    "reimbursements": []
                }
            
            # 获取当前小组的工作表
            worksheet = get_or_create_worksheet(sheet_handler, group_name)
            
            # 加载数据按钮
            col_refresh, col_empty = st.columns([1, 5])
            with col_refresh:
                if st.button("🔄 加载数据", key=f"grp_{group_name}_load_btn"):
                    with st.spinner("正在从Google Sheets加载数据..."):
                        data = load_group_data(worksheet)
                        st.session_state[f"grp_{group_name}_data"] = data
                        st.success("数据加载成功！")
            
            # 获取当前小组数据
            group_data = st.session_state[f"grp_{group_name}_data"]
            
            # 1. 小组成员管理
            st.subheader("👥 小组成员 (Group Members)")
            with st.container(border=True):
                # 显示成员列表
                if group_data["members"]:
                    st.dataframe(
                        pd.DataFrame(group_data["members"]),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("当前小组暂无成员，请添加成员")
                
                # 添加成员表单
                with st.expander("➕ 添加新成员", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("姓名", key=f"grp_{group_name}_member_name")
                        new_student_id = st.text_input("学号", key=f"grp_{group_name}_member_id")
                    with col2:
                        new_position = st.text_input("职位", key=f"grp_{group_name}_member_pos")
                        new_contact = st.text_input("联系方式", key=f"grp_{group_name}_member_contact")
                    
                    if st.button("确认添加", key=f"grp_{group_name}_add_member"):
                        if not all([new_name, new_student_id, new_position]):
                            st.error("请填写姓名、学号和职位（必填项）")
                        else:
                            # 检查学号重复
                            duplicate = any(
                                m["StudentID"] == new_student_id 
                                for m in group_data["members"]
                            )
                            if duplicate:
                                st.error("该学号已存在于成员列表中")
                            else:
                                # 更新本地数据
                                group_data["members"].append({
                                    "Name": new_name,
                                    "StudentID": new_student_id,
                                    "Position": new_position,
                                    "Contact": new_contact
                                })
                                # 保存到Google Sheets
                                if save_members(worksheet, group_data["members"]):
                                    st.success("成员添加成功！")
                                st.session_state[f"grp_{group_name}_data"] = group_data
            
            # 2. 小组收入管理
            st.subheader("💰 小组收入 (Group Earnings)")
            with st.container(border=True):
                # 显示收入列表
                if group_data["earnings"]:
                    earnings_df = pd.DataFrame(group_data["earnings"])
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
                    
                    # 显示总收入
                    total_earning = earnings_df["Amount"].sum()
                    st.markdown(f"**总收入: ¥{total_earning:.2f}**")
                else:
                    st.info("当前小组暂无收入记录")
                
                # 添加收入表单
                with st.expander("➕ 添加新收入", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        earn_date = st.date_input(
                            "日期", 
                            datetime.today(),
                            key=f"grp_{group_name}_earn_date"
                        )
                    with col2:
                        earn_amount = st.number_input(
                            "金额", 
                            min_value=0.01, 
                            step=0.01,
                            key=f"grp_{group_name}_earn_amt"
                        )
                    with col3:
                        earn_desc = st.text_input(
                            "描述",
                            key=f"grp_{group_name}_earn_desc"
                        )
                    
                    if st.button("确认添加", key=f"grp_{group_name}_add_earning"):
                        if not earn_desc:
                            st.error("请填写收入描述")
                        else:
                            # 更新本地数据
                            group_data["earnings"].append({
                                "Date": earn_date.strftime("%Y-%m-%d"),
                                "Amount": earn_amount,
                                "Description": earn_desc
                            })
                            # 保存到Google Sheets
                            if save_earnings(worksheet, group_data["earnings"]):
                                st.success("收入添加成功！")
                            st.session_state[f"grp_{group_name}_data"] = group_data
                
                # 删除收入功能
                if group_data["earnings"]:
                    earn_to_delete = st.selectbox(
                        "选择要删除的收入",
                        [f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" 
                         for e in group_data["earnings"]],
                        key=f"grp_{group_name}_del_earn",
                        index=None,
                        placeholder="选择收入项..."
                    )
                    
                    if st.button("删除选中收入", key=f"grp_{group_name}_del_earn_btn"):
                        if earn_to_delete:
                            # 过滤掉要删除的收入
                            group_data["earnings"] = [
                                e for e in group_data["earnings"]
                                if f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" != earn_to_delete
                            ]
                            # 保存到Google Sheets
                            if save_earnings(worksheet, group_data["earnings"]):
                                st.success("收入删除成功！")
                            st.session_state[f"grp_{group_name}_data"] = group_data
            
            # 3. 报销请求管理
            st.subheader("📋 报销请求 (Reimbursement Requests)")
            with st.container(border=True):
                # 显示报销列表
                if group_data["reimbursements"]:
                    st.dataframe(
                        pd.DataFrame(group_data["reimbursements"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # 显示总报销金额
                    total_reimburse = sum(r["Amount"] for r in group_data["reimbursements"])
                    st.markdown(f"**总报销金额: ¥{total_reimburse:.2f}**")
                else:
                    st.info("当前小组暂无报销请求")
                
                # 添加报销请求表单
                with st.expander("➕ 提交新报销请求", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        req_date = st.date_input(
                            "日期", 
                            datetime.today(),
                            key=f"grp_{group_name}_req_date"
                        )
                    with col2:
                        req_amount = st.number_input(
                            "金额", 
                            min_value=0.01, 
                            step=0.01,
                            key=f"grp_{group_name}_req_amt"
                        )
                    with col3:
                        req_desc = st.text_input(
                            "描述",
                            key=f"grp_{group_name}_req_desc"
                        )
                    
                    if st.button("提交请求", key=f"grp_{group_name}_add_req"):
                        if not req_desc:
                            st.error("请填写报销描述")
                        else:
                            # 更新本地数据
                            group_data["reimbursements"].append({
                                "Date": req_date.strftime("%Y-%m-%d"),
                                "Amount": req_amount,
                                "Description": req_desc,
                                "Status": "Pending"  # 默认状态为待处理
                            })
                            # 保存到Google Sheets
                            if save_reimbursements(worksheet, group_data["reimbursements"]):
                                st.success("报销请求提交成功！")
                            st.session_state[f"grp_{group_name}_data"] = group_data
                
                # 更新报销状态功能
                if group_data["reimbursements"]:
                    req_to_update = st.selectbox(
                        "选择要更新的报销请求",
                        [f"{r['Date']} - ¥{r['Amount']} - {r['Description']} ({r['Status']})" 
                         for r in group_data["reimbursements"]],
                        key=f"grp_{group_name}_upd_req",
                        index=None,
                        placeholder="选择报销项..."
                    )
                    
                    new_status = st.selectbox(
                        "更新状态为",
                        ["Pending", "Approved", "Rejected"],
                        key=f"grp_{group_name}_req_status"
                    )
                    
                    if st.button("更新状态", key=f"grp_{group_name}_upd_req_btn"):
                        if req_to_update:
                            # 更新状态
                            for req in group_data["reimbursements"]:
                                req_str = f"{req['Date']} - ¥{req['Amount']} - {req['Description']} ({req['Status']})"
                                if req_str == req_to_update:
                                    req["Status"] = new_status
                                    break
                            # 保存到Google Sheets
                            if save_reimbursements(worksheet, group_data["reimbursements"]):
                                st.success("报销状态更新成功！")
                            st.session_state[f"grp_{group_name}_data"] = group_data

# 调试用：直接运行模块时显示界面
if __name__ == "__main__":
    render_groups()
