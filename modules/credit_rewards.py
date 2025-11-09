# modules/credit_rewards.py
import streamlit as st
import sys
import os
import gspread

# 解决根目录导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 复用现有Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    st.header("🎓 学分信息列表")
    st.markdown("---")
    st.caption("数据实时同步自Google Sheets（表格：Student，工作表：credits 和 information）")

    try:
        # 1. 初始化工具类
        credentials_path = ""
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 2. 配置主表格名称
        spreadsheet_name = "Student"

        # 3. 打开主表格
        try:
            spreadsheet = gsheet.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            st.error(f"❌ 表格 '{spreadsheet_name}' 不存在")
            st.info("请检查是否存在名为'Student'的Google表格")
            return

        # ---------------------- 读取学分数据（credits工作表） ----------------------
        worksheet_credits = "credits"  # 学分数据工作表
        try:
            worksheet_1 = spreadsheet.worksheet(worksheet_credits)
            credit_data = gsheet.get_all_records(worksheet_1)
        except gspread.WorksheetNotFound:
            st.error(f"❌ 工作表 '{worksheet_credits}' 不存在")
            st.info("请在'Student'表格中创建名为'credits'的工作表")
            return

        # 显示学分数据
        if not credit_data:
            st.info(f"工作表 '{worksheet_credits}' 中暂无数据")
            return

        with st.container(height=450):
            st.dataframe(credit_data, use_container_width=True, hide_index=True)

        # ---------------------- 读取信息表数据（information工作表） ----------------------
        worksheet_info = "information"  # 信息表工作表（需在Google Sheet中创建）
        info_data = None
        try:
            worksheet_2 = spreadsheet.worksheet(worksheet_info)
            info_data = gsheet.get_all_records(worksheet_2)  # 从新工作表读取数据
        except gspread.WorksheetNotFound:
            st.warning(f"⚠️ 工作表 '{worksheet_info}' 不存在，将显示默认信息表")
            # 若工作表不存在，显示默认静态数据
            info_data = {
                "奖励内容": ["奶茶", "薯片", "咖啡店优惠券", "舞会门票"],
                "所需学分": [50, 30, 80, 150]
            }

        # ---------------------- 并排显示统计信息和信息表 ----------------------
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 统计信息")
            st.markdown(f"- 总记录数：**{len(credit_data)}**")
            # 可添加更多统计项，例如：
            # total_credits = sum(item.get("学分", 0) for item in credit_data)
            # st.markdown(f"- 总学分：**{total_credits}**")

        with col2:
            st.markdown("### Information（信息表）")
            if info_data:
                st.dataframe(info_data, use_container_width=True)
            else:
                st.info("信息表无数据")

    except Exception as e:
        st.error(f"错误：{str(e)}")
        st.info("排查步骤：\n1. 确认表格和工作表名称正确\n2. 确保服务账号有访问权限")

if __name__ == "__main__":
    render_credit_rewards()
