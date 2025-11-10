# google_drive_utils.py
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

class GoogleDriveHandler:
    def __init__(self, credentials):
        self.creds = credentials
        self.service = build('drive', 'v3', credentials=self.creds)
        # 替换为你的Google Drive文件夹ID（手动创建文件夹后获取）
        self.folder_id = "你的文件夹ID"  # 例如："1AbC2dEfG3hIjK4lMnOpQrStUvWxYz"

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
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            # 设置为公开可读
            self.service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except HttpError as e:
            st.error(f"Drive API错误: {str(e)}")
            return None
