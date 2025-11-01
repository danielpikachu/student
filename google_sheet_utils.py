# google_sheet_utils.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# 1. 配置授权（密钥文件路径为根目录的credentials.json）
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    # 本地运行：直接读取密钥文件
    credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
except:
    # 线上部署（如Streamlit Cloud）：从secrets读取密钥
    import json
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(st.secrets["credentials"]), scope
    )
client = gspread.authorize(credentials)

# 2. 连接到目标Google Sheet（替换为你的Sheet名称，如"学生会管理系统数据"）
SHEET_NAME = "StudentUnionData"
try:
    sheet = client.open(SHEET_NAME)
except gspread.exceptions.SpreadsheetNotFound:
    raise Exception(f"未找到名为{SHEET_NAME}的Google Sheet，请检查名称是否正确")


class GoogleSheetHandler:
    """Google Sheet操作工具类，供各模块调用"""
    @staticmethod
    def get_worksheet(module_name):
        """获取模块对应的分表（如Calendar模块对应"Calendar"分表）"""
        try:
            return sheet.worksheet(module_name)
        except gspread.exceptions.WorksheetNotFound:
            # 若分表不存在，自动创建（避免手动创建的麻烦）
            return sheet.add_worksheet(title=module_name, rows="1000", cols="20")

    @staticmethod
    def load_data(module_name):
        """从分表加载数据（返回列表，第一行为表头）"""
        worksheet = GoogleSheetHandler.get_worksheet(module_name)
        data = worksheet.get_all_values()
        # 若分表为空，返回空列表（各模块可自行初始化表头）
        return data if data else []

    @staticmethod
    def save_data(module_name, data):
        """将数据保存到分表（覆盖原有数据，确保实时同步）"""
        worksheet = GoogleSheetHandler.get_worksheet(module_name)
        worksheet.clear()  # 清空旧数据
        if data:  # 若数据非空，插入新数据
            worksheet.insert_rows(data, row=1)
