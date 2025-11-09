# modules/credit_rewards.py
import streamlit as st
import sys
import os
import gspread  # 用于捕获表格/工作表不存在的异常

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
    st.caption("数据实时同步自Google Sheets（表格名：Student，工作表名：credits）")

    try:
        # 1. 初始化工具类（确保认证正确）
        credentials_path = ""  # 根据工具类要求填写密钥路径
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 2. 配置表格和工作表信息（关键：使用表格名"Student"）
        spreadsheet_name = "Student"  # 表格名称（替换为你的实际表格名）
        worksheet_name = "credits"    # 工作表名称（已确认）

        # 3. 分步验证：先通过表格名打开表格
        try:
            # 若工具类支持通过名称打开表格，直接使用
            spreadsheet = gsheet.client.open(spreadsheet_name)  # 用表格名打开
            st.success(f"✅ 表格 '{spreadsheet_name}' 访问成功")
        except gspread.SpreadsheetNotFound:
            st.error(f"❌ 表格 '{spreadsheet_name}' 不存在，请检查表格名称是否正确")
            st.info("提示：确保Google Sheets中存在名为'Student'的表格，且未被重命名")
            return

        # 4. 验证工作表是否存在
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            st.success(f"✅ 工作表 '{worksheet_name}' 访问成功")
        except gspread.WorksheetNotFound:
            st.error(f"❌ 工作表 '{worksheet_name}' 不存在于表格 '{spreadsheet_name}' 中")
            st.info("提示：在'Student'表格中确认是否有名为'credits'的工作表（区分大小写）")
            return

        # 5. 读取数据（根据工具类方法调整参数）
        # 若工具类的get_all_records需要工作表对象，则传入worksheet
        credit_data = gsheet.get_all_records(worksheet)

        # 6. 显示数据
        if not credit_data:
            st.info(f"工作表 '{worksheet_name}' 中暂无数据，请在Google Sheets中添加内容后重试")
            return

        with st.container(height=450):
            st.dataframe(credit_data, use_container_width=True, hide_index=True)

        st.markdown(f"### 统计信息")
        st.markdown(f"- 总记录数：**{len(credit_data)}** 条")

    except Exception as e:
        st.error(f"其他错误：{str(e)}")
        st.info("排查步骤：\n1. 确认表格名是'Student'（区分大小写）\n2. 确认工作表名是'credits'\n3. 确认服务账号已被授予表格访问权限")

if __name__ == "__main__":
    render_credit_rewards()
