from __future__ import print_function
import io
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import json
import pandas as pd


# Definição de escopos (Tipos de autorização): TOTAL
SCOPES_DRIVE = ['https://www.googleapis.com/auth/drive']
KEY = 'client_secret.json'


def authentication():
    """
    Autenticação do Código. Conecta na API do Google
    Cria um arquivo Token do tipo JSON necessário para uso da API dispensando autenticação no navegador
    Retorna as credenciais
    """
    creds = None
    # Caso exista token.json, ele atribuirá VAR associando com os scopos
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES_DRIVE)

    # Caso não exista token.json OU se as credenciais não for inválidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Primeiro Login acontecendo, autenticação pelo navegador
            flow = InstalledAppFlow.from_client_secrets_file(KEY, SCOPES_DRIVE)
            creds = flow.run_local_server(port=0)
        # Criar o arquivo token.json
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def download_json_gdrive(service):
    try:
        # ID do arquivo JSON hospedado no Gdrive
        file_id = '1WaymK35JtvGMsHtjck4EFJlFUSyPfz8r'
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
          # print("Download %d%%." % int(status.progress() * 100))
        fh.seek(0)
        with open(os.path.join("/home/hercilio/Área de Trabalho/devcloud676/", "data.json"), 'wb') as f:
            f.write(fh.read())
            f.close()

    except HttpError as error:
        print(f'An error occurred: {error}')


def get_data_json():
    f = open('data.json')
    data = json.load(f)
    dataset = pd.DataFrame(data=data)
    return dataset


def file_create(dataset, service):
    # Cria arquivo do Excel
    dataset.to_excel('dados.xlsx', index=False)

    file_metadata = {
        "name": 'Planilha_123',
        "mimeType": 'application/vnd.google-apps.spreadsheet'
    }
    media = MediaFileUpload('dados.xlsx')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('Google Sheet ID: %s' % file.get('id'), "criada com sucesso!")
    id_file = file.get('id')
    if os.path.exists("dados.xlsx"):
        os.remove("dados.xlsx")
    if os.path.exists("data.json"):
        os.remove("data.json")


  # Retrieve the existing parents to remove
    file = service.files().get(fileId=id_file, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    file = service.files().update(fileId=id_file, addParents='1eLZLb5Oe3yI9QdgeouAuvRdFJIh3mdL3', removeParents=previous_parents, fields='id, parents').execute()
    service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=id_file).execute()


def check_sheet(service):
    page_token = None
    while True:
        response = service.files().list(q="name='planilha_123'", spaces='drive', fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()
        for file in response.get('files', []):
            print('Há uma mesma planilha criada: %s (%s)' % (file.get('name'), file.get('id')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return response


def main():
    creds = authentication()
    service = build('drive', 'v3', credentials=creds)
    download_json_gdrive(service)
    dataset = get_data_json()
    response = check_sheet(service)

    if len(response['files']) == 0:
        file_create(dataset, service)







main()
