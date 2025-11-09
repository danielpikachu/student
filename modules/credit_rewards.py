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
    """直接从Google Sheets读取并显示credits工作表内容（带滚动条）"""
    st.header("🎓 Credits List")
    st.markdown("---")
    st.info("数据实时同步自 Google Sheets，更新表格后刷新页面页面即可即可查看最新内容")

    # 1. 从Streamlit Secrets获取Google认证信息（修复AttrDict序列化问题）
    try:
        if 'google_credentials' in st.secrets:
            # 关键修复：提取AttrDict的原始字典数据
            creds_data = st.secrets['google_credentials']
            # 判断是否为AttrDict类型，是的话通过__dict__转换
            if hasattr(creds_data, '__dict__'):
                creds_dict = creds_data.__dict__
            else:
                creds_dict = dict(creds_data)
            # 创建认证对象
            credentials = Credentials.from_service_account_info(creds_dict)
        else:
            st.error("请在Streamlit Secrets中配置google_credentials")
            return
    except Exception as e:
        st.error(f"认证失败: {str(e)}")
        return

    # 2. 连接Google Sheets并读取credits工作表
    try:
        # 连接到Google Sheets
        client = gspread.authorize(credentials)
        # 替换为你的表格ID和工作表名称
        spreadsheet = client.open_by_key("你的表格ID").worksheet("credits")
        
        # 获取所有数据（包含表头）
        data = spreadsheet.get_all_records()
        if not data:
            st.warning("工作表中暂无数据")
            return

    except Exception as e:
        st.error(f"读取工作表失败: {str(e)}")
        return

    # 3. 带滚动条显示数据
    st.subheader("当前学分信息")
    with st.container(height=400):
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    st.markdown(f"**共 {len(data)} 条记录**")

if __name__ == "__main__":
    render_credit_rewards()
