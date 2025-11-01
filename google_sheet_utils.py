# google_sheet_utils.py（根目录）
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# 配置：替换为你的 Google Sheet 名称！
SHEET_NAME = "你的Google Sheet名称"  # 关键：必须与实际表格名称一致

# 授权范围
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 初始化客户端（增加详细错误处理）
def get_google_client():
    try:
        # 读取根目录的 credentials.json
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json",  # 确保文件在根目录
            scope
        )
        client = gspread.authorize(credentials)
        return client
    except FileNotFoundError:
        st.error("❌ 未找到 credentials.json 文件，请检查根目录是否存在该文件")
        return None
    except Exception as e:
        st.error(f"❌ 授权失败：{str(e)}")
        st.info("请检查密钥文件是否有效，或重新下载服务账号密钥")
        return None

# 初始化表格连接
client = get_google_client()
sheet = None
if client:
    try:
        # 打开指定名称的 Google Sheet（名称必须完全匹配）
        sheet = client.open(SHEET_NAME)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ 未找到名为「{SHEET_NAME}」的Google Sheet，请检查名称是否正确")
    except Exception as e:
        st.error(f"❌ 打开表格失败：{str(e)}")

class GoogleSheetHandler:
    @staticmethod
    def get_worksheet(worksheet_name):
        """获取指定分表，不存在则创建"""
        if not sheet:
            return None
        try:
            return sheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # 自动创建分表
            return sheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        except Exception as e:
            st.error(f"获取分表「{worksheet_name}」失败：{str(e)}")
            return None

    @staticmethod
    def load_data(worksheet_name):
        """加载分表数据"""
        worksheet = GoogleSheetHandler.get_worksheet(worksheet_name)
        if not worksheet:
            return []
        try:
            return worksheet.get_all_values()
        except Exception as e:
            st.error(f"加载数据失败：{str(e)}")
            return []

    @staticmethod
    def save_data(worksheet_name, data):
        """保存数据到分表"""
        worksheet = GoogleSheetHandler.get_worksheet(worksheet_name)
        if not worksheet:
            return False
        try:
            worksheet.clear()
            if data:
                worksheet.insert_rows(data, row=1)
            return True
        except Exception as e:
            st.error(f"保存数据失败：{str(e)}")
            return False
