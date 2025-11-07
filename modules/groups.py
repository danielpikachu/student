# modules/groups.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from googleapiclient.errors import HttpError

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
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
    .quota-warning {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def init_google_sheet_handler():
    """初始化Google Sheet处理器"""
    if "sheet_handler" in st.session_state:
        return st.session_state["sheet_handler"]
    
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        handler = GoogleSheetHandler(credentials_path=creds_path)
        st.session_state["sheet_handler"] = handler
        return handler
    except Exception as e:
        st.error(f"Google Sheets初始化失败: {str(e)}")
        return None

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=3, max=20),
    retry=retry_if_exception_type((HttpError, ConnectionError)),
    reraise=True
)
def get_worksheet_with_retry(sheet_handler, spreadsheet_name, worksheet_name):
    """带重试机制的工作表获取方法"""
    try:
        if "last_api_call" in st.session_state:
            elapsed = (datetime.now() - st.session_state["last_api_call"]).total_seconds()
            if elapsed < 2:
                time.sleep(2 - elapsed)
        
        worksheet = sheet_handler.get_worksheet(
            spreadsheet_name=spreadsheet_name,
            worksheet_name=worksheet_name
        )
        st.session_state["last_api_call"] = datetime.now()
        return worksheet
    except HttpError as e:
        st.session_state["last_api_call"] = datetime.now()
        if "429" in str(e):
            st.warning("检测到配额限制，正在延长等待时间...")
        raise

def get_group_worksheet(sheet_handler, group_name):
    """获取指定小组的子工作表（增强缓存机制）"""
    cache_key = f"worksheet_{group_name}"
    
    if cache_key in st.session_state:
        cache_entry = st.session_state[cache_key]
        if datetime.now() - cache_entry["time"] < timedelta(minutes=15):
            return cache_entry["worksheet"]
    
    if not sheet_handler:
        return None
    
    try:
        worksheet = get_worksheet_with_retry(
            sheet_handler,
            spreadsheet_name="Student",
            worksheet_name=group_name
        )
        st.session_state[cache_key] = {
            "worksheet": worksheet,
            "time": datetime.now()
        }
        return worksheet
    except HttpError as e:
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error(f"""获取{group_name}工作表失败: API请求配额已用尽，请等待1-2分钟后再尝试""")
        elif "404" in str(e):
            st.error(f"获取{group_name}工作表失败: 工作表不存在")
        else:
            st.error(f"获取{group_name}工作表失败: {str(e)}")
        return None
    except Exception as e:
        st.error(f"获取{group_name}工作表失败: {str(e)}")
        return None

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=3, max=20),
    retry=retry_if_exception_type((HttpError, ConnectionError)),
    reraise=True
)
def load_group_data_with_retry(worksheet):
    """带重试机制的小组数据加载"""
    if "last_api_call" in st.session_state:
        elapsed = (datetime.now() - st.session_state["last_api_call"]).total_seconds()
        if elapsed < 2:
            time.sleep(2 - elapsed)
    
    data = worksheet.get_all_values()
    st.session_state["last_api_call"] = datetime.now()
    return data

def load_group_data(worksheet):
    """从工作表加载小组数据"""
    if not worksheet:
        return {"members": [], "earnings": [], "reimbursements": []}
    
    try:
        all_data = load_group_data_with_retry(worksheet)
        data = {"members": [], "earnings": [], "reimbursements": []}
        current_section = None
        
        for row in all_data:
            if all(cell.strip() == "" for cell in row):
                continue
                
            stripped_first = row[0].strip()
            if stripped_first == "Members":
                current_section = "members"
                continue
            elif stripped_first == "Earnings":
                current_section = "earnings"
                continue
            elif stripped_first == "Reimbursements":
                current_section = "reimbursements"
                continue
            
            if stripped_first in ["Name", "Date"]:
                continue
            
            if current_section == "members":
                if row[0].strip() and row[1].strip():
                    data["members"].append({
                        "Name": row[0].strip(),
                        "StudentID": row[1].strip(),
                        "Position": row[2].strip() if len(row) > 2 else "",
                        "Contact": row[3].strip() if len(row) > 3 else ""
                    })
            elif current_section == "earnings":
                if row[0].strip() and row[1].strip():
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = row[0].strip()
                        st.warning(f"收入日期格式不正确: {row[0]}, 建议使用YYYY-MM-DD")
                    
                    data["earnings"].append({
                        "Date": formatted_date,
                        "Amount": float(row[1]) if row[1] else 0.0,
                        "Description": row[2].strip() if len(row) > 2 else ""
                    })
            elif current_section == "reimbursements":
                if row[0].strip() and row[1].strip():
                    try:
                        date_obj = datetime.strptime(row[0], "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        formatted_date = row[0].strip()
                        st.warning(f"报销日期格式不正确: {row[0]}, 建议使用YYYY-MM-DD")
                    
                    data["reimbursements"].append({
                        "Date": formatted_date,
                        "Amount": float(row[1]) if row[1] else 0.0,
                        "Description": row[2].strip() if len(row) > 2 else "",
                        "Status": row[3].strip() if len(row) > 3 else "Pending"
                    })
        
        return data
    except HttpError as e:
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error(f"加载数据失败: API请求配额已用尽，请等待1-2分钟后点击刷新按钮重试")
        else:
            st.error(f"加载小组数据失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}
    except Exception as e:
        st.error(f"加载小组数据失败: {str(e)}")
        return {"members": [], "earnings": [], "reimbursements": []}

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=3, max=20),
    retry=retry_if_exception_type((HttpError, ConnectionError)),
    reraise=True
)
def append_new_member(worksheet, new_member):
    """在Google Sheet的Members区域末尾追加新成员"""
    try:
        if "last_api_call" in st.session_state:
            elapsed = (datetime.now() - st.session_state["last_api_call"]).total_seconds()
            if elapsed < 3:
                time.sleep(3 - elapsed)
        
        all_values = worksheet.get_all_values()  # 0-based索引
        section_row = None  # 区域标题所在行（1-based）
        
        # 查找Members区域标题行
        for i, row in enumerate(all_values, 1):
            if row[0].strip() == "Members":
                section_row = i
                break
        
        if not section_row:
            st.error("未找到Members区域")
            return False
        
        # 数据区域起始行（1-based）：标题行+2（跳过标题和表头）
        data_start_1based = section_row + 2
        total_rows = len(all_values)
        
        # 查找数据区域的最后一行（非空行）
        last_data_row = data_start_1based - 1  # 默认为表头行下方
        for i in range(data_start_1based - 1, total_rows):  # 0-based遍历
            if all(cell.strip() == "" for cell in all_values[i]):
                break
            last_data_row = i + 1  # 转换为1-based
        
        # 准备新成员数据
        new_row = [
            new_member["Name"],
            new_member["StudentID"],
            new_member["Position"],
            new_member["Contact"]
        ]
        
        # 在最后一行后面插入新成员
        worksheet.insert_rows([new_row], last_data_row + 1)
        st.session_state["last_api_call"] = datetime.now()
        return True
    except Exception as e:
        st.session_state["last_api_call"] = datetime.now()
        raise

# 关键修改：重写删除函数，确保只删除不添加
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=3, max=20),
    retry=retry_if_exception_type((HttpError, ConnectionError)),
    reraise=True
)
def delete_specific_member(worksheet, student_id_to_delete):
    """仅删除Google Sheet中指定StudentID的成员，不进行任何添加操作"""
    try:
        # 1. 控制API调用频率
        if "last_api_call" in st.session_state:
            elapsed = (datetime.now() - st.session_state["last_api_call"]).total_seconds()
            if elapsed < 3:
                time.sleep(3 - elapsed)
        
        # 2. 获取当前工作表所有数据
        all_values = worksheet.get_all_values()  # 0-based索引
        section_row = None  # Members标题行（1-based）
        
        # 3. 精确定位Members区域
        for i, row in enumerate(all_values, 1):
            if row[0].strip() == "Members":
                section_row = i
                break
        
        if not section_row:
            st.error("未找到Members区域")
            return False
        
        # 4. 计算数据区域范围（跳过标题行和表头行）
        header_row_0based = section_row  # 表头行（"Name", "StudentID"所在行）
        data_start_0based = section_row + 1  # 实际数据开始行（0-based）
        
        # 5. 查找要删除的行（精确匹配StudentID）
        rows_to_delete = []
        for i in range(data_start_0based, len(all_values)):
            row = all_values[i]
            if len(row) >= 2 and row[1].strip() == student_id_to_delete:
                # 转换为1-based行号
                rows_to_delete.append(i + 1)
        
        if not rows_to_delete:
            st.warning(f"未找到学号为 {student_id_to_delete} 的成员")
            return False
        
        # 6. 从下往上删除，避免行号偏移
        for row_num in reversed(rows_to_delete):
            worksheet.delete_rows(row_num)
            time.sleep(1.5)  # 延长等待时间确保删除完成
        
        # 7. 不进行任何插入操作，仅删除
        st.session_state["last_api_call"] = datetime.now()
        return True
    except Exception as e:
        st.session_state["last_api_call"] = datetime.now()
        raise

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=3, max=20),
    retry=retry_if_exception_type((HttpError, ConnectionError)),
    reraise=True
)
def update_worksheet_section(worksheet, section_title, new_data):
    """更新工作表区域（用于收入和报销）"""
    try:
        if "last_api_call" in st.session_state:
            elapsed = (datetime.now() - st.session_state["last_api_call"]).total_seconds()
            if elapsed < 3:
                time.sleep(3 - elapsed)
        
        all_values = worksheet.get_all_values()
        section_row = None
        
        for i, row in enumerate(all_values, 1):
            if row[0].strip() == section_title:
                section_row = i
                break
        
        if not section_row:
            st.error(f"未找到区域: {section_title}")
            return False
        
        data_start_1based = section_row + 2
        total_rows = len(all_values)
        
        if data_start_1based <= total_rows:
            worksheet.delete_rows(data_start_1based, total_rows - data_start_1based + 1)
        
        if new_data:
            non_empty_rows = [row for row in new_data if any(cell.strip() for cell in row)]
            if non_empty_rows:
                worksheet.insert_rows(non_empty_rows, data_start_1based)
        
        st.session_state["last_api_call"] = datetime.now()
        return True
    except Exception as e:
        st.session_state["last_api_call"] = datetime.now()
        raise

def save_earnings(worksheet, earnings):
    if not worksheet or not earnings:
        return False
        
    try:
        rows_to_insert = [
            [e["Date"], e["Amount"], e["Description"], ""]
            for e in earnings
        ]
        return update_worksheet_section(worksheet, "Earnings", rows_to_insert)
    except HttpError as e:
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error(f"更新收入失败: API配额已用尽，请稍后重试")
        else:
            st.error(f"保存收入数据失败: {str(e)}")
        return False
    except Exception as e:
        st.error(f"保存收入数据失败: {str(e)}")
        return False

def save_reimbursements(worksheet, reimbursements):
    if not worksheet or not reimbursements:
        return False
        
    try:
        rows_to_insert = [
            [r["Date"], r["Amount"], r["Description"], r["Status"]]
            for r in reimbursements
        ]
        return update_worksheet_section(worksheet, "Reimbursements", rows_to_insert)
    except HttpError as e:
        if "429" in str(e) or "Quota exceeded" in str(e):
            st.error(f"更新报销失败: API配额已用尽，请稍后重试")
        else:
            st.error(f"保存报销数据失败: {str(e)}")
        return False
    except Exception as e:
        st.error(f"保存报销数据失败: {str(e)}")
        return False

def render_groups():
    add_custom_css()
    st.header("👥 小组管理 (Groups Management)")
    st.write("管理小组成员、收入和报销请求")
    
    st.markdown("""
    <div class="quota-warning">
    <strong>注意:</strong> Google Sheets API有请求频率限制，请避免频繁操作。
    如遇配额超限，请等待1-2分钟后再操作。
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    sheet_handler = init_google_sheet_handler()
    
    group_names = [f"Group{i}" for i in range(1, 9)]
    tabs = st.tabs(group_names)
    
    if "last_api_call" not in st.session_state:
        st.session_state["last_api_call"] = datetime.min
    
    for i, tab in enumerate(tabs):
        group_name = group_names[i]
        with tab:
            # 初始化会话状态
            if f"grp_{group_name}_data" not in st.session_state:
                st.session_state[f"grp_{group_name}_data"] = {
                    "members": [], "earnings": [], "reimbursements": []
                }
            
            if f"grp_{group_name}_last_loaded" not in st.session_state:
                st.session_state[f"grp_{group_name}_last_loaded"] = datetime.min
            
            worksheet = get_group_worksheet(sheet_handler, group_name)
            
            now = datetime.now()
            # 自动加载数据（15分钟缓存）
            if (now - st.session_state[f"grp_{group_name}_last_loaded"] > timedelta(minutes=15) or 
                f"grp_{group_name}_loaded" not in st.session_state):
                with st.spinner(f"正在自动加载{group_name}的数据..."):
                    data = load_group_data(worksheet)
                    st.session_state[f"grp_{group_name}_data"] = data
                    st.session_state[f"grp_{group_name}_loaded"] = True
                    st.session_state[f"grp_{group_name}_last_loaded"] = now
                    st.success(f"{group_name}数据加载成功！")
            
            # 手动刷新按钮
            col_refresh, col_empty = st.columns([1, 5])
            with col_refresh:
                if st.button("🔄 刷新数据", key=f"grp_{group_name}_load_btn"):
                    last_refresh = st.session_state.get(f"grp_{group_name}_last_refresh", datetime.min)
                    if now - last_refresh < timedelta(seconds=30):
                        st.warning("请不要频繁刷新，至少间隔30秒")
                    else:
                        with st.spinner("正在从Google Sheets刷新数据..."):
                            data = load_group_data(worksheet)
                            st.session_state[f"grp_{group_name}_data"] = data
                            st.session_state[f"grp_{group_name}_last_loaded"] = now
                            st.session_state[f"grp_{group_name}_last_refresh"] = now
                            st.success("数据刷新成功！")
            
            group_data = st.session_state[f"grp_{group_name}_data"]
            
            # 小组成员管理
            st.subheader("👥 小组成员 (Group Members)")
            with st.container(border=True):
                if group_data["members"]:
                    st.dataframe(
                        pd.DataFrame(group_data["members"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # 成员删除功能 - 关键修改点
                    member_to_delete = st.selectbox(
                        "选择要删除的成员",
                        [f"{m['Name']} - {m['StudentID']}" for m in group_data["members"]],
                        key=f"grp_{group_name}_del_member",
                        index=None,
                        placeholder="选择成员..."
                    )
                    
                    if st.button("删除选中成员", key=f"grp_{group_name}_del_member_btn"):
                        if member_to_delete and worksheet:
                            # 提取要删除的StudentID
                            student_id_to_delete = member_to_delete.split(" - ")[1].strip()
                            
                            # 保存当前成员列表用于恢复
                            current_members = group_data["members"].copy()
                            
                            # 更新本地缓存
                            original_count = len(group_data["members"])
                            group_data["members"] = [
                                m for m in group_data["members"]
                                if m["StudentID"].strip() != student_id_to_delete
                            ]
                            
                            if len(group_data["members"]) < original_count:
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("成员已从界面移除，正在同步到Google Sheet...")
                                
                                # 执行删除（仅删除，无任何添加操作）
                                try:
                                    if delete_specific_member(worksheet, student_id_to_delete):
                                        st.success("成员已成功从Google Sheet删除！")
                                    else:
                                        # 恢复本地数据
                                        group_data["members"] = current_members
                                        st.session_state[f"grp_{group_name}_data"] = group_data
                                        st.error("删除操作未成功执行")
                                except Exception as e:
                                    # 恢复本地数据
                                    group_data["members"] = current_members
                                    st.session_state[f"grp_{group_name}_data"] = group_data
                                    st.error(f"删除失败: {str(e)}")
                else:
                    st.info("当前小组暂无成员，请添加成员")
                
                # 添加新成员
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
                            # 检查本地重复
                            duplicate = any(m["StudentID"].strip() == new_student_id.strip() 
                                          for m in group_data["members"])
                            if duplicate:
                                st.error("该学号已存在于成员列表中")
                            elif worksheet:
                                new_member = {
                                    "Name": new_name.strip(), 
                                    "StudentID": new_student_id.strip(),
                                    "Position": new_position.strip(), 
                                    "Contact": new_contact.strip()
                                }
                                current_members = group_data["members"].copy()
                                group_data["members"].append(new_member)
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("成员已添加到界面，正在同步到Google Sheet...")
                                
                                try:
                                    if append_new_member(worksheet, new_member):
                                        st.success("成员已成功添加到Google Sheet！")
                                    else:
                                        group_data["members"] = current_members
                                        st.session_state[f"grp_{group_name}_data"] = group_data
                                        st.error("添加操作未成功执行")
                                except Exception as e:
                                    group_data["members"] = current_members
                                    st.session_state[f"grp_{group_name}_data"] = group_data
                                    st.error(f"添加失败: {str(e)}")
            
            # 小组收入管理（未修改）
            st.subheader("💰 小组收入 (Group Earnings)")
            with st.container(border=True):
                if group_data["earnings"]:
                    earnings_df = pd.DataFrame(group_data["earnings"])
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
                    total_earning = earnings_df["Amount"].sum()
                    st.markdown(f"**总收入: ¥{total_earning:.2f}**")
                else:
                    st.info("当前小组暂无收入记录")
                
                with st.expander("➕ 添加新收入", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        earn_date = st.date_input("日期", datetime.today(), key=f"grp_{group_name}_earn_date")
                    with col2:
                        earn_amount = st.number_input("金额", min_value=0.01, step=0.01, key=f"grp_{group_name}_earn_amt")
                    with col3:
                        earn_desc = st.text_input("描述", key=f"grp_{group_name}_earn_desc")
                    
                    if st.button("确认添加", key=f"grp_{group_name}_add_earning"):
                        if not earn_desc:
                            st.error("请填写收入描述")
                        elif worksheet:
                            new_earning = {
                                "Date": earn_date.strftime("%Y-%m-%d"),
                                "Amount": earn_amount,
                                "Description": earn_desc.strip()
                            }
                            group_data["earnings"].append(new_earning)
                            st.session_state[f"grp_{group_name}_data"] = group_data
                            st.success("收入已添加到界面，正在同步到Google Sheet...")
                            
                            with st.spinner("正在同步..."):
                                if save_earnings(worksheet, group_data["earnings"]):
                                    st.success("收入已成功同步！")
                
                if group_data["earnings"]:
                    earn_to_delete = st.selectbox(
                        "选择要删除的收入",
                        [f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" for e in group_data["earnings"]],
                        key=f"grp_{group_name}_del_earn",
                        index=None,
                        placeholder="选择收入项..."
                    )
                    
                    if st.button("删除选中收入", key=f"grp_{group_name}_del_earn_btn"):
                        if earn_to_delete and worksheet:
                            original_count = len(group_data["earnings"])
                            group_data["earnings"] = [
                                e for e in group_data["earnings"]
                                if f"{e['Date']} - ¥{e['Amount']} - {e['Description']}" != earn_to_delete
                            ]
                            
                            if len(group_data["earnings"]) < original_count:
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("收入已从界面移除，正在同步...")
                                
                                with st.spinner("正在同步..."):
                                    if save_earnings(worksheet, group_data["earnings"]):
                                        st.success("收入已成功删除！")
            
            # 报销请求管理（未修改）
            st.subheader("📋 报销请求 (Reimbursement Requests)")
            with st.container(border=True):
                if group_data["reimbursements"]:
                    st.dataframe(
                        pd.DataFrame(group_data["reimbursements"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    total_reimburse = sum(r["Amount"] for r in group_data["reimbursements"])
                    st.markdown(f"**总报销金额: ¥{total_reimburse:.2f}**")
                else:
                    st.info("当前小组暂无报销请求")
                
                with st.expander("➕ 提交新报销请求", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        req_date = st.date_input("日期", datetime.today(), key=f"grp_{group_name}_req_date")
                    with col2:
                        req_amount = st.number_input("金额", min_value=0.01, step=0.01, key=f"grp_{group_name}_req_amt")
                    with col3:
                        req_desc = st.text_input("描述", key=f"grp_{group_name}_req_desc")
                    
                    if st.button("提交请求", key=f"grp_{group_name}_add_req"):
                        if not req_desc:
                            st.error("请填写报销描述")
                        elif worksheet:
                            new_reimbursement = {
                                "Date": req_date.strftime("%Y-%m-%d"),
                                "Amount": req_amount,
                                "Description": req_desc.strip(),
                                "Status": "Pending"
                            }
                            group_data["reimbursements"].append(new_reimbursement)
                            st.session_state[f"grp_{group_name}_data"] = group_data
                            st.success("报销请求已添加到界面，正在同步...")
                            
                            with st.spinner("正在同步..."):
                                if save_reimbursements(worksheet, group_data["reimbursements"]):
                                    st.success("报销请求已成功同步！")
                
                if group_data["reimbursements"]:
                    req_to_update = st.selectbox(
                        "选择要更新的报销请求",
                        [f"{r['Date']} - ¥{r['Amount']} - {r['Description']} ({r['Status']})" for r in group_data["reimbursements"]],
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
                        if req_to_update and worksheet:
                            updated = False
                            for req in group_data["reimbursements"]:
                                req_str = f"{req['Date']} - ¥{req['Amount']} - {req['Description']} ({req['Status']})"
                                if req_str == req_to_update and req["Status"] != new_status:
                                    req["Status"] = new_status
                                    updated = True
                                    break
                            
                            if updated:
                                st.session_state[f"grp_{group_name}_data"] = group_data
                                st.success("报销状态已更新，正在同步...")
                                
                                with st.spinner("正在同步..."):
                                    if save_reimbursements(worksheet, group_data["reimbursements"]):
                                        st.success("报销状态已成功同步！")

if __name__ == "__main__":
    render_groups()
