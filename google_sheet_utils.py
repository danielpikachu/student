import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from typing import List, Dict, Optional, Any


class GoogleSheetHandler:
    """Google Sheets 操作工具类，封装认证和工作表操作"""
    
    def __init__(self, credentials_path: Optional[str] = None, scope: Optional[List[str]] = None):
        self.credentials_path = credentials_path
        # 默认可用权限：读写工作表
        self.scope = scope or [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = self._authorize()  # 初始化时完成授权

    def _authorize(self) -> gspread.Client:
        """
        授权并创建客户端连接
        优先从Streamlit Secrets读取凭证，也支持从本地文件读取（开发环境）
        """
        try:
            # 尝试从Streamlit Secrets获取配置（生产环境）
            creds_dict = st.secrets.get("google_credentials")
            if creds_dict:
                return gspread.authorize(
                    Credentials.from_service_account_info(creds_dict, scopes=self.scope)
                )
            
            # 从本地文件读取凭证（开发环境）
            if self.credentials_path:
                return gspread.authorize(
                    Credentials.from_service_account_file(self.credentials_path, scopes=self.scope)
                )
            
            raise ValueError("未找到有效的凭证配置，请检查Streamlit Secrets或提供凭证文件路径")
            
        except Exception as e:
            st.error(f"授权失败: {str(e)}")
            raise

    def get_spreadsheet(self, spreadsheet_id: Optional[str] = None, spreadsheet_name: Optional[str] = None) -> gspread.Spreadsheet:
        """
        获取表格对象
        支持通过表格ID（更可靠）或表格名称获取
        """
        if not spreadsheet_id and not spreadsheet_name:
            raise ValueError("必须提供spreadsheet_id或spreadsheet_name")
            
        try:
            if spreadsheet_id:
                return self.client.open_by_key(spreadsheet_id)
            return self.client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            identifier = spreadsheet_id or spreadsheet_name
            raise Exception(f"表格不存在: {identifier}")
        except Exception as e:
            raise Exception(f"获取表格失败: {str(e)}")

    def get_worksheet(self, 
                    spreadsheet: gspread.Spreadsheet, 
                    worksheet_name: Optional[str] = None,
                    worksheet_index: Optional[int] = None) -> gspread.Worksheet:
        """
        获取指定表格中的工作表
        支持通过名称或索引获取
        """
        if not worksheet_name and worksheet_index is None:
            raise ValueError("必须提供worksheet_name或worksheet_index")
            
        try:
            if worksheet_name:
                return spreadsheet.worksheet(worksheet_name)
            return spreadsheet.get_worksheet(worksheet_index)
        except gspread.WorksheetNotFound:
            identifier = worksheet_name or worksheet_index
            raise Exception(f"工作表不存在: {identifier}")
        except Exception as e:
            raise Exception(f"获取工作表失败: {str(e)}")

    def get_all_records(self, worksheet: gspread.Worksheet, head: int = 1) -> List[Dict[str, Any]]:
        """
        获取工作表所有记录（字典列表）
        :param head: 表头所在行索引（从1开始）
        """
        return worksheet.get_all_records(head=head)

    def append_record(self, worksheet: gspread.Worksheet, data: List[Any], value_input_option: str = "USER_ENTERED") -> None:
        """
        向工作表追加一行记录
        :param value_input_option: 输入值处理方式，USER_ENTERED会自动转换格式
        """
        worksheet.append_row(data, value_input_option=value_input_option)

    def delete_record_by_value(self, worksheet: gspread.Worksheet, value: Any, col: Optional[int] = None) -> bool:
        """
        根据值删除对应行
        :param col: 限制搜索的列（None表示搜索所有列）
        :return: 是否成功删除
        """
        try:
            cell = worksheet.find(value, in_column=col)
            if cell:
                worksheet.delete_rows(cell.row)
                return True
            return False
        except gspread.CellNotFound:
            return False  # 未找到值，无需删除
        except Exception as e:
            raise Exception(f"删除记录失败: {str(e)}")

    def update_cell(self, worksheet: gspread.Worksheet, row: int, col: int, value: Any, value_input_option: str = "USER_ENTERED") -> None:
        """更新指定单元格的值"""
        worksheet.update_cell(row, col, value, value_input_option=value_input_option)

    def batch_update(self, worksheet: gspread.Worksheet, data: List[Dict[str, Any]]) -> None:
        """
        批量更新单元格
        data格式: [{'range': 'A1:B2', 'values': [[1,2], [3,4]]}, ...]
        """
        worksheet.batch_update(data)

    def clear_worksheet(self, worksheet: gspread.Worksheet, range_name: Optional[str] = None) -> None:
        """清空工作表内容（保留表头）"""
        if range_name:
            worksheet.clear(range_name=range_name)
        else:
            # 从第二行开始清空（保留表头）
            worksheet.clear(range_name=f"A2:{worksheet.get_addr_int(worksheet.row_count, worksheet.col_count)}")
