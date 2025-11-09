# modules/credit_rewards.py
import streamlit as st
import sys
import os

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
    st.caption("数据实时同步自Google Sheets，更新表格后刷新页面即可查看最新内容")

    try:
        # 1. 初始化工具类（传入必要的credentials_path参数）
        # 根据工具类要求，若需要密钥路径则填写，否则传空
        credentials_path = ""  # 或工具类要求的密钥路径
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 2. 先获取工作表对象（分开传递表格ID和工作表名）
        spreadsheet_id = "你的Google表格ID"  # 替换为实际ID
        worksheet_name = "credits"           # 替换为实际工作表名
        worksheet = gsheet.get_worksheet(spreadsheet_id, worksheet_name)  # 假设get_worksheet支持2个参数

        # 3. 调用get_all_records()，只传1个参数（工作表对象或无参数，根据工具类定义）
        # 关键修复：根据错误提示，该方法只接受2个参数（含self），所以这里只传worksheet
        credit_data = gsheet.get_all_records(worksheet)  # 适配工具类的参数要求

        # 4. 处理无数据情况
        if not credit_data:
            st.info("当前工作表中暂无数据，请在Google Sheets中添加内容后重试")
            return

        # 5. 带滚动条显示数据
        st.subheader("当前学分记录")
        with st.container(height=450):
            st.dataframe(
                credit_data,
                use_container_width=True,
                hide_index=True
            )

        # 6. 统计信息
        st.markdown(f"### 统计信息")
        st.markdown(f"- 总记录数：**{len(credit_data)}** 条")

    except Exception as e:
        st.error(f"数据加载失败：{str(e)}")
        st.info("提示：请检查工具类方法参数是否匹配，或联系管理员确认google_sheet_utils.py的用法")

if __name__ == "__main__":
    render_credit_rewards()
