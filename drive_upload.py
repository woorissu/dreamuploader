from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

# 서비스 계정 키 파일
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

# Google Drive API 클라이언트 생성
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# ✅ 최상위 폴더 ID (모든 사용자 폴더를 이 안에 만들고 싶을 경우)
ROOT_FOLDER_ID = '1anl7IJV7GoFSIkLNo7l2j4X22dydUnIK'  # ← 여기에 고객별 폴더가 들어감

def get_or_create_folder(folder_name, parent_folder_id=None):
    """Drive에서 폴더 이름으로 검색, 없으면 생성 후 ID 반환"""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"

    response = drive_service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()

    files = response.get('files', [])
    if files:
        return files[0]['id']

    # 없으면 새로 생성
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]

    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def upload_to_drive(local_path, drive_filename, customer_folder_name):
    """주문자 이름 폴더에 동일 파일명이 있으면 삭제 후 업로드"""
    
    # 1. 고객 폴더 만들거나 찾기
    folder_id = get_or_create_folder(customer_folder_name, ROOT_FOLDER_ID)

    # 2. 기존 동일 파일명이 있는지 확인하고 삭제
    query = f"'{folder_id}' in parents and name = '{drive_filename}' and trashed = false"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    for file in response.get('files', []):
        drive_service.files().delete(fileId=file['id']).execute()
        print(f"🗑 기존 파일 삭제: {file['id']}")

    # 3. 새 파일 업로드
    file_metadata = {
        'name': drive_filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(local_path, resumable=True)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"✅ 업로드 완료: {drive_filename} → 폴더: {customer_folder_name}, 파일 ID: {uploaded_file['id']}")
