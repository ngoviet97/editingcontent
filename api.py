from __future__ import print_function
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import os
import glob
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from google.cloud import translate_v2
import pickle
from googleapiclient import errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SERVICE_ACCOUNT_FILE = '/Volumes/Root/Webify/Apps/v1/key/key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = None
spreadsheet_credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# The ID and range of a sample spreadsheet.
spreadsheet_service = build('sheets', 'v4', credentials=spreadsheet_credentials)
sheet = spreadsheet_service.spreadsheets()

drive_credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive'])
delegated_credentials = drive_credentials.with_subject('py-googlesheet-v1@tough-timing-350303.iam.gserviceaccount.com')
drive_service = build('drive', 'v3', credentials=delegated_credentials)
mime_types = ['application/vnd.ms-excel']
def get_data(SAMPLE_SPREADSHEET_ID,SAMPLE_RANGE_NAME):
    # Call the Sheets API
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values')
    return values
def request_data(SAMPLE_SPREADSHEET_ID,SAMPLE_RANGE_NAME,data):
    request = sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, valueInputOption="USER_ENTERED", body={"values":data}).execute()
    return request
def clear_data(SAMPLE_SPREADSHEET_ID,SAMPLE_RANGE_NAME):
    clear = sheet.values().clear(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME).execute()
    return clear
def append_data(SAMPLE_SPREADSHEET_ID,APPEND_RANGE,DATA,mode=None):
    if mode == 'OVERWRITE':
        append = sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=APPEND_RANGE, valueInputOption='USER_ENTERED', insertDataOption="OVERWRITE", body={"values":DATA}).execute()

    elif mode == 'INSERT_ROWS':
        append = sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=APPEND_RANGE, valueInputOption='USER_ENTERED', insertDataOption="INSERT_ROWS", body={"values":DATA}).execute()

    return append
def create_folder(FolderID=None,FolderName=None):
    file_metadata = {
    'name': FolderName,
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [FolderID]}

    drive = drive_service.files().create(body=file_metadata).execute()
    return drive
def upload_file(FolderID=None):
    FilePath = '/Volumes/Root/Webify/Filter data/IMG'
    file_name = os.path.basename(FilePath)
    directory = "ExtractDate"

    # Parent Directory path
    parent_dir = FilePath

    # Path
    path_create = os.path.join(parent_dir, directory)
    try:
        os.mkdir(path_create)
    except:
        pass
    # csv files in the path
    file_list = glob.glob(FilePath + "/*.jpg")
    file_metadata = {'name': file_name,
                     'parents': [FolderID]
                     }

    for file in file_list:
        try:
            media = MediaFileUpload(file, mimetype='image/jpeg')
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print("File {} is uploading at folder ID {}".format(file,FolderID))
        except:
            pass

    for f in file_list:
        os.remove(f)
def list_files_folders(Folder_ID):
    query = f"parents = '{Folder_ID}'"
    resonpse = drive_service.files().list(pageSize=1000,q=query).execute()
    files = resonpse.get('files')
    nextPageToken = resonpse.get('nextPageToken')

    while nextPageToken:
        resonpse = drive_service.files().list(q=query).execute()
        files.extend(resonpse.get('files'))
        nextPageToken = resonpse.get('nextPageToken')

    pd.set_option('display.max_columns',100)
    pd.set_option('display.max_rows',500)
    pd.set_option('display.min_rows',500)
    pd.set_option('display.max_colwidth',150)
    pd.set_option('display.width',200)
    pd.set_option('expand_frame_repr',True)
    df = pd.DataFrame(files)
    list_Data = []
    try:
        for x,z in zip(list(df['name']),list(df['id'])):
            list_Data.append([x,z])
        return list_Data
    except:
        return None
def indexing_url(url):
    SCOPE_INDEX = ["https://www.googleapis.com/auth/indexing"]
    ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"

    # service_account_file.json is the private key that you created for your service account.
    credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scopes=SCOPE_INDEX)

    http = credentials.authorize(httplib2.Http())

    content = str({
      "url": url,
      "type": "URL_UPDATED"
    })
    print(content)
    response, content = http.request(ENDPOINT, method="POST", body=content)
    print(response)
    print(content)
def Translate(target, text, model="nmt"):
    """Translates text into the target language.

    Make sure your project is allowlisted.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

    translate_client = translate_v2.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.translate(text, target_language=target, model=model)
    returndata = str(result['translatedText'].replace("&#39;","'"))

    return returndata
