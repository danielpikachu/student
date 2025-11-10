# google_drive_utils.py
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from io import BytesIO  # 新增：处理文件流

class GoogleDriveHandler:
    def __init__(self, credentials):
        self.creds = credentials
        self.service = build('drive', 'v3', credentials=self.creds)
        # 确保此处是你共享文件夹的正确ID（从个人Drive地址栏复制）
        self.folder_id = "1NDgg27Q_XIn0p7XVBKg_uxaGwqRgdpqY"

    def upload_image(self, image_file, group_code):
        """上传图片到个人共享文件夹（核心修正版）"""
        filename = f"{group_code}-receipt-{image_file.name}"
        # 1. 关键修正：强制文件归属到你的共享文件夹
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id],  # 必须绑定到你的文件夹
            'mimeType': image_file.type
        }
        # 2. 关键修正：正确处理Streamlit上传的文件流（避免文件读取失败）
        media = MediaIoBaseUpload(
            BytesIO(image_file.getvalue()),  # 转换为服务端可识别的流
            mimetype=image_file.type,
            resumable=True
        )
        try:
            # 3. 确保API调用支持个人Drive
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=False  # 个人Drive无需启用共享驱动器支持
            ).execute()
            
            # 4. 简化权限设置（仅允许读取，避免权限过高导致的问题）
            self.service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'},
                supportsAllDrives=False
            ).execute()
            
            return f"https://drive.google.com/uc?export=view&id={file['id']}"
        except HttpError as e:
            # 详细错误提示，帮助排查
            st.error(f"Drive API错误: {str(e)}")
            st.error(f"请检查：1. 文件夹ID是否正确；2. 服务账号是否为文件夹编辑者；3. 文件夹是否存在")
            return None
