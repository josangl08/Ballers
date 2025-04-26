# controllers/sheets_controller.py
import os
import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

# Configuración de Google Sheets
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SHEET_KEY = os.getenv("GSPREAD_SHEET_KEY")  # ID del spreadsheet

@st.cache_resource
def get_gspread_client():
    """
    Crea y devuelve el cliente de gspread autenticado.
    """
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(credentials)
    return client

@st.cache_data
def get_financials():
    """
    Lee el sheet de gastos e ingresos y devuelve un DataFrame de pandas.
    """
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_KEY).sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df