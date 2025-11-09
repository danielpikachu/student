# modules/credit_rewards.py
import streamlit as st
import sys
import os
import json
from google.oauth2.service_account import Credentials
import gspread

# 解决根目录导入问题
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def render_credit_rewards():
    st.header("🎓 Credits List")
    st.markdown("---")
    st.info("数据实时同步自 Google Sheets，更新表格后刷新页面即可查看最新内容")

    # 1. 从环境变量读取认证信息（无需修改Streamlit Secrets）
    try:
        # 环境变量名称自定义（例如：GOOGLE_CREDS_JSON）
        creds_json = os.getenv("GOOGLE_CREDS_JSON")
        if not creds_json:
            st.error("未检测到环境变量GOOGLE_CREDS_JSON，请配置后重试")
            return

        # 解析JSON字符串为字典
        creds_dict = json.loads(creds_json)
        
        # 验证关键字段
        required_fields = ["client_email", "token_uri", "private_key"]
        for field in required_fields:
            if field not in creds_dict:
                st.error(f"认证信息缺少必要字段: {field}")
                return

    except json.JSONDecodeError:
        st.error("环境变量中的JSON格式错误，请检查")
        return
    except Exception as e:
        st.error(f"读取认证信息失败: {str(e)}")
        return

    # 2. 创建认证对象
    try:
        credentials = Credentials.from_service_account_info(creds_dict)
    except Exception as e:
        st.error(f"认证对象创建失败: {str(e)}")
        return

    # 3. 连接Google Sheets并读取credits工作表
    try:
        client = gspread.authorize(credentials)
        # 替换为你的表格ID和工作表名称
        spreadsheet = client.open_by_key("你的表格ID").worksheet("credits")
        data = spreadsheet.get_all_records()

        if not data:
            st.warning("工作表中暂无数据")
            return

    except Exception as e:
        st.error(f"读取工作表失败: {str(e)}")
        return

    # 4. 带滚动条显示数据
    st.subheader("当前学分信息")
    with st.container(height=400):
        st.dataframe(data, use_container_width=True, hide_index=True)

    st.markdown(f"**共 {len(data)} 条记录**")

if __name__ == "__main__":
    render_credit_rewards()
