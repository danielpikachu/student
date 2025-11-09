# modules/credit_rewards.py
import streamlit as st
import sys
import os

# 解决根目录导入问题（google_sheet_utils与modules同级）
current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前模块目录
parent_dir = os.path.dirname(current_dir)  # 父目录（与google_sheet_utils同级）
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 复用现有Google Sheets工具类
from google_sheet_utils import GoogleSheetHandler

def render_credit_rewards():
    """渲染学分列表模块，实时同步Google Sheets的credits工作表数据"""
    # 页面标题与说明
    st.header("🎓 学分信息列表")
    st.markdown("---")
    st.caption("数据实时同步自Google Sheets，更新表格后刷新页面即可查看最新内容")

    try:
        # 1. 初始化工具类（复用现有认证配置，无需修改Secrets）
        gsheet = GoogleSheetHandler()

        # 2. 读取credits工作表数据（替换为你的表格ID）
        spreadsheet_id = "你的Google表格ID"  # 例如："1Abcdefg1234567890hijklmnopqrstuvwxyz"
        worksheet_name = "credits"  # 目标工作表名称
        credit_data = gsheet.get_all_records(spreadsheet_id, worksheet_name)

        # 3. 处理无数据情况
        if not credit_data:
            st.info("当前工作表中暂无数据，请在Google Sheets中添加内容后重试")
            return

        # 4. 带滚动条显示数据（适配46条记录）
        st.subheader("当前学分记录")
        with st.container(height=450):  # 固定高度，超出自动显示滚动条
            st.dataframe(
                credit_data,
                use_container_width=True,  # 自适应容器宽度
                hide_index=True,  # 隐藏默认索引列
                column_config={  # 优化列显示（可根据实际表头调整）
                    "姓名": st.column_config.TextColumn(width="medium"),
                    "学号": st.column_config.TextColumn(width="small"),
                    "学分": st.column_config.NumberColumn(width="small"),
                    "更新时间": st.column_config.DatetimeColumn(width="medium")
                }
            )

        # 5. 显示统计信息
        st.markdown(f"### 统计信息")
        st.markdown(f"- 总记录数：**{len(credit_data)}** 条")
        # 如需其他统计（如总学分），可在此添加：
        # total_credits = sum(item.get("学分", 0) for item in credit_data)
        # st.markdown(f"- 总学分：**{total_credits}** 分")

    except Exception as e:
        # 捕获异常但不影响其他模块
        st.error(f"数据加载失败：{str(e)}")
        st.info("请检查Google SheetsID、工作表名称是否正确，或联系管理员")

# 测试运行（本地调试用）
if __name__ == "__main__":
    render_credit_rewards()
