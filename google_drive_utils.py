# google_drive_utils.py
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

class GoogleDriveHandler:
    def __init__(self, credentials):
        self.creds = credentials
        # 1. 关键修改：添加supportsAllDrives=True参数（兼容个人驱动器）
        self.service = build('drive', 'v3', credentials=self.creds, supportsAllDrives=True)
        # 你的个人驱动器文件夹ID（保持不变）
        self.folder_id = "1NDgg27Q_XIn0p7XVBKg_uxaGwqRgdpqY"

    def upload_image(self, image_file, group_code):
        """上传图片到指定文件夹并返回可访问链接"""
        filename = f"{group_code}-receipt-{image_file.name}"
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id],
            'mimeType': image_file.type
        }
        media = MediaIoBaseUpload(image_file, mimetype=image_file.type, resumable=True)
        try:
            # 2. 关键修改：添加supportsAllDrives=True参数
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True  # 允许操作个人驱动器
            ).execute()
            
            # 设置权限时同样添加该参数
            self.service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'},
                supportsAllDrives=True
            ).execute()
            
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except HttpError as e:
            st.error(f"Drive API错误: {str(e)}")
            return None
