from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import os

SERVICE_ACCOUNT_FILE = '/etc/secrets/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

ROOT_FOLDER_ID = '1anl7IJV7GoFSIkLNo7l2j4X22dydUnIK'  # ← 수정 필요시 여기에

def get_or_create_folder(folder_name, parent_folder_id=None):
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

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]

    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

def upload_to_drive(file_stream, drive_filename, customer_folder_name):
    folder_id = get_or_create_folder(customer_folder_name, ROOT_FOLDER_ID)

    query = f"'{folder_id}' in parents and name = '{drive_filename}' and trashed = false"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    for file in response.get('files', []):
        drive_service.files().delete(fileId=file['id']).execute()
        print(f"🗑 기존 파일 삭제: {file['id']}")

    file_metadata = {
        'name': drive_filename,
        'parents': [folder_id]
    }

    media = MediaIoBaseUpload(file_stream, mimetype='image/jpeg', resumable=True)

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    print(f"✅ 업로드 완료: {drive_filename} → 폴더: {customer_folder_name}, 파일 ID: {uploaded_file['id']}")
