# modules/credit_rewards.py
import streamlit as st
import sys
import os
import json

# 解决根目录导入问题（google_sheet_utils与modules同级）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 复用现有Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    """渲染学分列表模块，适配需要credentials_path参数的GoogleSheetHandler"""
    st.header("🎓 学分信息列表")
    st.markdown("---")
    st.caption("数据实时同步自Google Sheets，更新表格后刷新页面即可查看最新内容")

    try:
        # 1. 处理GoogleSheetHandler需要的credentials_path参数
        # 方案：从Secrets读取认证信息，生成临时路径（或传递空路径兼容工具类）
        if 'google_credentials' in st.secrets:
            # 从Secrets获取认证信息并转换为字典
            creds_data = st.secrets['google_credentials']
            creds_dict = dict(creds_data) if not isinstance(creds_data, dict) else creds_data
            
            # 生成临时JSON内容（工具类可能需要文件路径）
            temp_creds_path = os.path.join(parent_dir, "temp_creds.json")
            with open(temp_creds_path, "w") as f:
                json.dump(creds_dict, f)
            credentials_path = temp_creds_path
        else:
            # 若工具类允许空路径（依赖本地文件），可传递空字符串
            credentials_path = ""

        # 2. 初始化工具类（传入required的credentials_path参数）
        gsheet = GoogleSheetHandler(credentials_path=credentials_path)

        # 3. 读取credits工作表数据（替换为你的表格ID）
        spreadsheet_id = "你的Google表格ID"  # 例如："1Abcdefg1234567890hijklmnopqrstuvwxyz"
        worksheet_name = "credits"
        credit_data = gsheet.get_all_records(spreadsheet_id, worksheet_name)

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

        # 6. 显示统计信息
        st.markdown(f"### 统计信息")
        st.markdown(f"- 总记录数：**{len(credit_data)}** 条")

    except Exception as e:
        st.error(f"数据加载失败：{str(e)}")
        st.info("请检查表格ID、工作表名称是否正确，或认证信息是否配置")
    finally:
        # 清理临时文件（如果生成了的话）
        if 'temp_creds_path' in locals() and os.path.exists(temp_creds_path):
            os.remove(temp_creds_path)

if __name__ == "__main__":
    render_credit_rewards()
