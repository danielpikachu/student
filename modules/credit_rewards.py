# modules/credit_rewards.py
import streamlit as st
from datetime import datetime
import uuid
import sys
import os
import json
from google.oauth2.service_account import Credentials

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    """渲染学分奖励模块界面（cre_前缀命名空间）"""
    st.header("🎓 Credit Rewards")
    st.markdown("---")
    
    # 初始化Google Sheets连接（使用Streamlit Cloud密钥）
    sheet_handler = None
    rewards_sheet = None
    try:
        # 从Streamlit Secrets获取认证信息
        if 'google_credentials' in st.secrets:
            # 解析JSON字符串为字典
            creds_dict = json.loads(st.secrets['google_credentials'])
            # 创建认证对象
            credentials = Credentials.from_service_account_info(creds_dict)
            # 初始化GoogleSheetHandler
            sheet_handler = GoogleSheetHandler(credentials=credentials)
            
            # 获取工作表
            rewards_sheet = sheet_handler.get_worksheet(
                spreadsheet_name="Student",
                worksheet_name="CreditRewards"
            )
        else:
            st.error("未配置Google认证信息，请检查Streamlit Secrets")
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")
    
    # 从Google Sheets同步数据（使用cre_records状态）
    if rewards_sheet and sheet_handler and (not st.session_state.get("cre_records")):
        try:
            all_data = rewards_sheet.get_all_values()
            expected_headers = ["uuid", "date", "student_id", "student_name", "reward_points", "reason", "handler"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                rewards_sheet.clear()
                rewards_sheet.append_row(expected_headers)
                records = []
            else:
                # 处理数据（跳过表头）
                records = [
                    {
                        "uuid": row[0],
                        "date": datetime.strptime(row[1], "%Y-%m-%d").date(),
                        "student_id": row[2],
                        "student_name": row[3],
                        "reward_points": int(row[4]),
                        "reason": row[5],
                        "handler": row[6]
                    } 
                    for row in all_data[1:] 
                    if row[0]  # 确保UUID不为空
                ]
            
            st.session_state.cre_records = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")
    
    # 初始化状态（防止首次加载时出错）
    if "cre_records" not in st.session_state:
        st.session_state.cre_records = []
    
    # ---------------------- 学分奖励记录展示 ----------------------
    st.subheader("Reward Records")
    if not st.session_state.cre_records:
        st.info("No credit reward records yet")
    else:
        # 定义列宽比例
        col_widths = [0.3, 1.0, 1.2, 1.5, 1.2, 2.5, 1.5, 1.0]
        
        # 显示固定表头
        header_cols = st.columns(col_widths)
        with header_cols[0]:
            st.write("**#**")
        with header_cols[1]:
            st.write("**Date**")
        with header_cols[2]:
            st.write("**Student ID**")
        with header_cols[3]:
            st.write("**Student Name**")
        with header_cols[4]:
            st.write("**Points**")
        with header_cols[5]:
            st.write("**Reason**")
        with header_cols[6]:
            st.write("**Handled By**")
        with header_cols[7]:
            st.write("**Action**")
        
        st.markdown("---")
        
        # 创建滚动容器
        scroll_container = st.container(height=320)
        with scroll_container:
            # 遍历显示每条记录
            for idx, record in enumerate(st.session_state.cre_records, 1):
                unique_key = f"cre_delete_{idx}_{record['uuid']}"
                cols = st.columns(col_widths)
                
                with cols[0]:
                    st.write(idx)
                with cols[1]:
                    st.write(record["date"].strftime("%Y-%m-%d"))
                with cols[2]:
                    st.write(record["student_id"])
                with cols[3]:
                    st.write(record["student_name"])
                with cols[4]:
                    st.write(record["reward_points"])
                with cols[5]:
                    st.write(record["reason"])
                with cols[6]:
                    st.write(record["handler"])
                with cols[7]:
                    if st.button(
                        "🗑️ Delete", 
                        key=unique_key,
                        use_container_width=True,
                        type="secondary"
                    ):
                        # 从本地状态删除
                        st.session_state.cre_records.pop(idx - 1)
                        
                        # 同步删除Google Sheets记录
                        if rewards_sheet and sheet_handler:
                            try:
                                cell = rewards_sheet.find(record["uuid"])
                                if cell:
                                    rewards_sheet.delete_rows(cell.row)
                                st.success(f"Record {idx} deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"同步删除失败: {str(e)}")
                
                # 行分隔线
                st.markdown("---")
        
        # 显示汇总信息
        total_points = sum(r["reward_points"] for r in st.session_state.cre_records)
        student_count = len(set(r["student_id"] for r in st.session_state.cre_records))
        
        st.markdown(f"""
        <div style='margin-top: 1rem; padding: 1rem; background-color: #f8f9fa; border-radius: 8px;'>
            <strong>Summary:</strong><br>
            Total Reward Points Distributed: {total_points} | 
            Number of Students Rewarded: {student_count}
        </div>
        """, unsafe_allow_html=True)
    
    st.write("=" * 50)
    
    # ---------------------- 新增学分奖励记录 ----------------------
    st.subheader("Record New Credit Reward")
    col1, col2 = st.columns(2)
    
    with col1:
        record_date = st.date_input(
            "Record Date", 
            value=datetime.today(),
            key="cre_input_date"
        )
        
        student_id = st.text_input(
            "Student ID", 
            value="",
            key="cre_input_id"
        ).strip()
        
        student_name = st.text_input(
            "Student Name", 
            value="",
            key="cre_input_name"
        ).strip()
    
    with col2:
        reward_points = st.number_input(
            "Reward Points", 
            min_value=1, 
            step=1, 
            value=10,
            key="cre_input_points"
        )
        
        reason = st.text_input(
            "Reason for Reward", 
            value="Academic excellence",
            key="cre_input_reason"
        ).strip()
        
        handler = st.text_input(
            "Handled By", 
            value="",
            key="cre_input_handler"
        ).strip()
    
    # 记录按钮
    if st.button("Record Reward", key="cre_btn_record", use_container_width=True, type="primary"):
        # 验证必填字段
        if not student_id or not student_name or not reason or not handler:
            st.error("Student ID, Name, Reason and Handler are required fields!")
            return
        
        # 创建新记录
        new_record = {
            "uuid": str(uuid.uuid4()),  # 生成唯一标识
            "date": record_date,
            "student_id": student_id,
            "student_name": student_name,
            "reward_points": reward_points,
            "reason": reason,
            "handler": handler
        }
        
        # 更新本地状态
        st.session_state.cre_records.append(new_record)
        
        # 同步到Google Sheets
        if rewards_sheet and sheet_handler:
            try:
                rewards_sheet.append_row([
                    new_record["uuid"],
                    new_record["date"].strftime("%Y-%m-%d"),
                    new_record["student_id"],
                    new_record["student_name"],
                    str(new_record["reward_points"]),
                    new_record["reason"],
                    new_record["handler"]
                ])
                st.success("Credit reward recorded successfully!")
                st.rerun()
            except Exception as e:
                st.warning(f"同步到Google Sheets失败: {str(e)}")
