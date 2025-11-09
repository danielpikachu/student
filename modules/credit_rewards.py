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
    st.info("数据实时同步自 Google Sheets，更新表格后刷新页面即可查看最新内容")

    # 1. 从Streamlit Secrets获取Google认证信息
    try:
        if 'google_credentials' in st.secrets:
            # 处理认证信息格式（兼容AttrDict）
            creds_json = json.dumps(st.secrets['google_credentials'])
            creds_dict = json.loads(creds_json)
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
        # 替换为你的表格名称（或表格ID）和工作表名称
        spreadsheet = client.open("你的表格名称").worksheet("credits")  # 核心：直接读取credits工作表
        
        # 获取所有数据（包含表头）
        data = spreadsheet.get_all_records()  # 自动将表头作为字典键，行数据作为值
        if not data:
            st.warning("工作表中暂无数据")
            return

    except Exception as e:
        st.error(f"读取工作表失败: {str(e)}")
        return

    # 3. 带滚动条显示数据（固定高度，超出自动滚动）
    st.subheader("当前学分信息")
    with st.container(height=400):  # 高度可调整，适配46条数据
        # 以表格形式展示（自动适配列宽）
        st.dataframe(
            data,
            use_container_width=True,  # 适应容器宽度
            hide_index=True  # 隐藏默认索引列
        )

    # 显示数据统计
    st.markdown(f"**共 {len(data)} 条记录**")

if __name__ == "__main__":
    render_credit_rewards()
