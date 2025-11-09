# modules/credit_rewards.py
import streamlit as st
from datetime import datetime
import sys
import os

# 解决根目录模块导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 导入Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

# 自定义CSS样式
def add_custom_css():
    st.markdown("""
    <style>
    .reward-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .reward-header {
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    .reward-points {
        color: #27ae60;
        font-weight: bold;
    }
    .total-points {
        font-size: 1.2rem;
        font-weight: bold;
        color: #3498db;
    }
    </style>
    """, unsafe_allow_html=True)

def render_credit_rewards():
    """渲染积分奖励模块界面（cr_前缀命名空间）"""
    add_custom_css()
    st.header("🎁 Credit Rewards System")
    st.divider()

    # 初始化Google Sheets连接
    sheet_handler = None
    rewards_sheet = None
    try:
        creds_path = os.path.join(ROOT_DIR, "credentials.json")
        sheet_handler = GoogleSheetHandler(credentials_path=creds_path)
        rewards_sheet = sheet_handler.get_worksheet(
            spreadsheet_name="Student",
            worksheet_name="CreditRewards"
        )
    except Exception as e:
        st.error(f"Google Sheets 初始化失败: {str(e)}")

    # 从Google Sheets同步数据（使用cr_rewards状态）
    if rewards_sheet and sheet_handler:
        try:
            all_data = rewards_sheet.get_all_values()
            expected_headers = ["student_id", "student_name", "points", "reason", "date"]
            
            # 检查表头
            if not all_data or all_data[0] != expected_headers:
                rewards_sheet.clear()
                rewards_sheet.append_row(expected_headers)
                records = []
            else:
                # 处理数据（跳过表头）
                records = [
                    {
                        "student_id": row[0],
                        "student_name": row[1],
                        "points": int(row[2]) if row[2].isdigit() else 0,
                        "reason": row[3],
                        "date": datetime.strptime(row[4], "%Y-%m-%d").date() if row[4] else None
                    } 
                    for row in all_data[1:] 
                    if row[0] and row[1]  # 确保学生ID和姓名不为空
                ]
            
            # 更新会话状态
            st.session_state.cr_rewards = records
        except Exception as e:
            st.warning(f"数据同步失败: {str(e)}")

    # 初始化会话状态（如果不存在）
    if "cr_rewards" not in st.session_state:
        st.session_state.cr_rewards = []

    # 显示总积分统计
    total_points = sum(reward["points"] for reward in st.session_state.cr_rewards)
    st.markdown(f"### Total Reward Points: <span class='total-points'>{total_points}</span>", unsafe_allow_html=True)
    st.divider()

    # 显示积分记录列表
    st.subheader("Recent Reward Records")
    
    # 按日期排序（最新的在前）
    sorted_rewards = sorted(
        st.session_state.cr_rewards,
        key=lambda x: x["date"] or datetime.min.date(),
        reverse=True
    )
    
    # 显示前10条记录
    for reward in sorted_rewards[:10]:
        with st.container():
            st.markdown(f"""
            <div class='reward-card'>
                <div class='reward-header'>{reward['student_name']} ({reward['student_id']})</div>
                <div>Points: <span class='reward-points'>{reward['points']}</span></div>
                <div>Reason: {reward['reason']}</div>
                <div>Date: {reward['date'].strftime('%Y-%m-%d') if reward['date'] else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)

    # 管理员操作区域
    st.divider()
    if st.session_state.auth_is_admin:
        with st.container(border=True):
            st.subheader("📝 Manage Reward Records")
            
            # 表单输入
            col1, col2 = st.columns(2)
            with col1:
                student_id = st.text_input("Student ID", placeholder="Enter student ID")
                student_name = st.text_input("Student Name", placeholder="Enter student name")
            
            with col2:
                points = st.number_input("Points", min_value=1, value=10)
                record_date = st.date_input("Date", value=datetime.today())
            
            reason = st.text_area(
                "Reason for Reward", 
                placeholder="Enter reason for this reward",
                max_chars=200
            )
            
            # 操作按钮
            col_save, col_delete = st.columns(2)
            with col_save:
                if st.button("💾 Save Record", use_container_width=True, type="primary", key="cr_btn_save"):
                    if not all([student_id, student_name, reason]):
                        st.error("Please fill in all required fields!")
                        return
                    
                    # 准备新记录
                    new_record = {
                        "student_id": student_id,
                        "student_name": student_name,
                        "points": points,
                        "reason": reason,
                        "date": record_date
                    }
                    
                    # 更新本地状态
                    st.session_state.cr_rewards.append(new_record)
                    
                    # 同步到Google Sheets
                    if rewards_sheet and sheet_handler:
                        try:
                            rewards_sheet.append_row([
                                student_id,
                                student_name,
                                str(points),
                                reason,
                                record_date.strftime("%Y-%m-%d")
                            ])
                            st.success("✅ Record saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"同步到Google Sheets失败: {str(e)}")
            
            with col_delete:
                if st.button("🗑️ Delete Record", use_container_width=True, key="cr_btn_delete"):
                    if not student_id:
                        st.error("Please enter Student ID to delete record")
                        return
                    
                    # 查找要删除的记录
                    to_delete = [
                        r for r in st.session_state.cr_rewards 
                        if r["student_id"] == student_id and 
                           r["date"] == record_date
                    ]
                    
                    if not to_delete:
                        st.warning("No matching record found!")
                        return
                    
                    # 更新本地状态
                    st.session_state.cr_rewards = [
                        r for r in st.session_state.cr_rewards 
                        if not (r["student_id"] == student_id and r["date"] == record_date)
                    ]
                    
                    # 同步删除Google Sheets记录
                    if rewards_sheet and sheet_handler:
                        try:
                            all_rows = rewards_sheet.get_all_values()
                            for i, row in enumerate(all_rows[1:], start=2):
                                if row[0] == student_id and row[4] == record_date.strftime("%Y-%m-%d"):
                                    rewards_sheet.delete_rows(i)
                            st.success("✅ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"从Google Sheets删除失败: {str(e)}")
