import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# 页面配置
st.set_page_config(page_title="小组财务管理系统", layout="wide")
st.title("📊 小组财务管理系统")

# ------------------------------
# 1. 谷歌表格连接配置
# ------------------------------
# 权限范围
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# 连接谷歌表格
@st.cache_resource
def connect_to_gsheets():
    try:
        # 从Streamlit Secrets获取凭证
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPE
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"连接谷歌表格失败: {str(e)}")
        return None

# 初始化连接
client = connect_to_gsheets()

# ------------------------------
# 2. 数据加载与解析函数（核心修复）
# ------------------------------
def load_group_data(worksheet):
    """加载并解析工作表数据，正确区分成员/收入/报销区域"""
    if not worksheet:
        return {"members": [], "earnings": [], "reimbursements": []}
    
    try:
        all_data = worksheet.get_all_values()
        data = {"members": [], "earnings": [], "reimbursements": []}
        current_section = None  # 当前解析的区域
        skip_next_row = False   # 用于跳过表头行
        
        for row in all_data:
            # 跳过空行
            if all(cell.strip() == "" for cell in row):
                continue
            
            # 识别区域标题行（切换区域并标记跳过表头）
            if row[0] == "Members":
                current_section = "members"
                skip_next_row = True
                continue
            elif row[0] == "Earnings":
                current_section = "earnings"
                skip_next_row = True
                continue
            elif row[0] == "Reimbursements":
                current_section = "reimbursements"
                skip_next_row = True
                continue
            
            # 跳过表头行
            if skip_next_row:
                skip_next_row = False
                continue
            
            # 解析当前区域数据（严格区分区域）
            if current_section == "members" and len(row) >= 4:
                data["members"].append({
                    "Name": row[0],
                    "StudentID": row[1],
                    "Position": row[2],
                    "Contact": row[3]
                })
            elif current_section == "earnings" and len(row) >= 3:
                # 日期格式化处理
                try:
                    date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = row[0]
                    st.warning(f"收入日期格式错误: {row[0]}（建议YYYY-MM-DD）")
                
                data["earnings"].append({
                    "Date": formatted_date,
                    "Amount": float(row[1]) if row[1] else 0.0,
                    "Description": row[2]
                })
            elif current_section == "reimbursements" and len(row) >= 4:
                # 日期格式化处理
                try:
                    date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = row[0]
                    st.warning(f"报销日期格式错误: {row[0]}（建议YYYY-MM-DD）")
                
                data["reimbursements"].append({
                    "Date": formatted_date,
                    "Amount": float(row[1]) if row[1] else 0.0,
                    "Description": row[2],
                    "Status": row[3] if row[3] in ["Pending", "Approved", "Rejected"] else "Pending"
                })
        
        return data
    except Exception as e:
        st.error(f"数据解析失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}

# ------------------------------
# 3. 数据保存函数
# ------------------------------
def save_to_worksheet(worksheet, data):
    """将数据保存到工作表，按区域结构化存储"""
    if not worksheet:
        st.error("无法保存数据：工作表连接失败")
        return False
    
    try:
        # 清空现有数据
        worksheet.clear()
        all_rows = []
        
        # 添加成员区域
        if data["members"]:
            all_rows.append(["Members", "", "", ""])  # 区域标题
            all_rows.append(["Name", "StudentID", "Position", "Contact"])  # 表头
            for member in data["members"]:
                all_rows.append([
                    member["Name"],
                    member["StudentID"],
                    member["Position"],
                    member["Contact"]
                ])
            all_rows.append(["", "", "", ""])  # 区域间隔
        
        # 添加收入区域
        if data["earnings"]:
            all_rows.append(["Earnings", "", "", ""])  # 区域标题
            all_rows.append(["Date", "Amount", "Description", ""])  # 表头
            for earning in data["earnings"]:
                all_rows.append([
                    earning["Date"],
                    str(earning["Amount"]),
                    earning["Description"],
                    ""
                ])
            all_rows.append(["", "", "", ""])  # 区域间隔
        
        # 添加报销区域
        if data["reimbursements"]:
            all_rows.append(["Reimbursements", "", "", ""])  # 区域标题
            all_rows.append(["Date", "Amount", "Description", "Status"])  # 表头
            for reimbursement in data["reimbursements"]:
                all_rows.append([
                    reimbursement["Date"],
                    str(reimbursement["Amount"]),
                    reimbursement["Description"],
                    reimbursement["Status"]
                ])
        
        # 写入工作表
        if all_rows:
            worksheet.insert_rows(all_rows, row=1)
        st.success("数据已成功保存！")
        return True
    except Exception as e:
        st.error(f"保存数据失败: {str(e)}")
        return False

# ------------------------------
# 4. 主界面逻辑
# ------------------------------
if client:
    # 选择或创建表格
    spreadsheet_name = st.text_input("输入表格名称（如：GroupFinance）", "GroupFinance")
    if st.button("确认/创建表格"):
        try:
            # 尝试打开表格，不存在则创建
            spreadsheet = client.open(spreadsheet_name)
            st.success(f"已打开表格: {spreadsheet_name}")
        except gspread.exceptions.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)
            st.success(f"已创建新表格: {spreadsheet_name}")
            # 共享表格（可选：添加编辑权限）
            # spreadsheet.share("your-email@gmail.com", perm_type="user", role="writer")
        
        # 存储表格信息到session_state
        st.session_state["spreadsheet"] = spreadsheet
        st.rerun()

    # 选择工作表（标签页）
    if "spreadsheet" in st.session_state:
        spreadsheet = st.session_state["spreadsheet"]
        worksheet_list = [ws.title for ws in spreadsheet.worksheets()]
        selected_worksheet = st.selectbox("选择小组工作表", worksheet_list)
        
        # 创建新工作表
        new_worksheet_name = st.text_input("创建新工作表（如：Group1）")
        if st.button("创建新工作表") and new_worksheet_name:
            if new_worksheet_name not in worksheet_list:
                spreadsheet.add_worksheet(title=new_worksheet_name, rows=100, cols=20)
                st.success(f"已创建工作表: {new_worksheet_name}")
                st.rerun()
            else:
                st.warning("工作表名称已存在！")
        
        # 加载选中的工作表数据
        worksheet = spreadsheet.worksheet(selected_worksheet)
        if st.button("🔄 加载数据"):
            st.session_state["group_data"] = load_group_data(worksheet)
            st.success("数据加载完成！")
            st.rerun()

        # 初始化数据（如果未加载）
        if "group_data" not in st.session_state:
            st.session_state["group_data"] = {"members": [], "earnings": [], "reimbursements": []}
        
        group_data = st.session_state["group_data"]

        # ------------------------------
        # 5. 成员管理模块
        # ------------------------------
        st.subheader("👥 小组成员管理")
        with st.expander("添加新成员", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_name = st.text_input("姓名")
            with col2:
                new_student_id = st.text_input("学号")
            with col3:
                new_position = st.text_input("职位")
            with col4:
                new_contact = st.text_input("联系方式")
            
            if st.button("添加成员") and all([new_name, new_student_id]):
                group_data["members"].append({
                    "Name": new_name,
                    "StudentID": new_student_id,
                    "Position": new_position,
                    "Contact": new_contact
                })
                st.success(f"已添加成员: {new_name}")
                st.session_state["group_data"] = group_data

        # 显示成员列表
        if group_data["members"]:
            members_df = pd.DataFrame(group_data["members"])
            st.dataframe(members_df, use_container_width=True)
            
            # 删除成员功能
            del_idx = st.selectbox("选择要删除的成员索引", range(len(group_data["members"])), format_func=lambda x: group_data["members"][x]["Name"])
            if st.button("删除选中成员"):
                del group_data["members"][del_idx]
                st.success("成员已删除")
                st.session_state["group_data"] = group_data
                st.rerun()
        else:
            st.info("暂无成员数据，请添加成员")

        # ------------------------------
        # 6. 收入管理模块
        # ------------------------------
        st.subheader("💰 收入管理")
        with st.expander("添加新收入", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                earn_date = st.date_input("日期", datetime.today()).strftime("%Y-%m-%d")
            with col2:
                earn_amount = st.number_input("金额", min_value=0.0, step=0.01)
            with col3:
                earn_desc = st.text_input("描述")
            
            if st.button("添加收入") and earn_amount > 0 and earn_desc:
                group_data["earnings"].append({
                    "Date": earn_date,
                    "Amount": earn_amount,
                    "Description": earn_desc
                })
                st.success(f"已添加收入: {earn_amount} 元")
                st.session_state["group_data"] = group_data

        # 显示收入列表
        if group_data["earnings"]:
            earnings_df = pd.DataFrame(group_data["earnings"])
            st.dataframe(earnings_df, use_container_width=True)
            total_earnings = sum(item["Amount"] for item in group_data["earnings"])
            st.info(f"总收入: {total_earnings:.2f} 元")
            
            # 删除收入功能
            del_earn_idx = st.selectbox("选择要删除的收入索引", range(len(group_data["earnings"])), format_func=lambda x: f"{group_data['earnings'][x]['Date']} - {group_data['earnings'][x]['Amount']}元")
            if st.button("删除选中收入"):
                del group_data["earnings"][del_earn_idx]
                st.success("收入记录已删除")
                st.session_state["group_data"] = group_data
                st.rerun()
        else:
            st.info("暂无收入数据，请添加收入")

        # ------------------------------
        # 7. 报销管理模块
        # ------------------------------
        st.subheader("🧾 报销管理")
        with st.expander("添加新报销", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                reimb_date = st.date_input("报销日期", datetime.today()).strftime("%Y-%m-%d")
            with col2:
                reimb_amount = st.number_input("报销金额", min_value=0.0, step=0.01)
            with col3:
                reimb_desc = st.text_input("报销描述")
            with col4:
                reimb_status = st.selectbox("状态", ["Pending", "Approved", "Rejected"])
            
            if st.button("添加报销") and reimb_amount > 0 and reimb_desc:
                group_data["reimbursements"].append({
                    "Date": reimb_date,
                    "Amount": reimb_amount,
                    "Description": reimb_desc,
                    "Status": reimb_status
                })
                st.success(f"已添加报销: {reimb_amount} 元")
                st.session_state["group_data"] = group_data

        # 显示报销列表
        if group_data["reimbursements"]:
            reimbursements_df = pd.DataFrame(group_data["reimbursements"])
            st.dataframe(reimbursements_df, use_container_width=True)
            total_reimbursed = sum(item["Amount"] for item in group_data["reimbursements"] if item["Status"] == "Approved")
            st.info(f"已批准报销总额: {total_reimbursed:.2f} 元")
            
            # 删除报销功能
            del_reimb_idx = st.selectbox("选择要删除的报销索引", range(len(group_data["reimbursements"])), format_func=lambda x: f"{group_data['reimbursements'][x]['Date']} - {group_data['reimbursements'][x]['Amount']}元")
            if st.button("删除选中报销"):
                del group_data["reimbursements"][del_reimb_idx]
                st.success("报销记录已删除")
                st.session_state["group_data"] = group_data
                st.rerun()
        else:
            st.info("暂无报销数据，请添加报销")

        # 保存数据按钮
        if st.button("💾 保存所有数据", type="primary"):
            save_to_worksheet(worksheet, group_data)

else:
    st.error("请检查谷歌表格凭证配置后重试")
