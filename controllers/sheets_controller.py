# controllers/sheets_controller.py

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SERVICE_ACCOUNT, SHEET_KEY

def get_financials():
    # Definimos SCOPES para Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Cargamos las credenciales
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT, scope)
    client = gspread.authorize(creds)

    # Abrimos el archivo por ID
    sheet = client.open_by_key(SHEET_KEY)
    worksheet = sheet.sheet1  # Primer pestaña

    # Descargamos los datos
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df
