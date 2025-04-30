# controllers/sheets_controller.py
import os
import pandas as pd
import gspread
from google.oauth2 import service_account
import logging
import streamlit as st
from config import GOOGLE_SHEET_ID, SERVICE_ACCOUNT  # Importar directamente de config.py

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flag para indicar si estamos en modo offline/fallback
sheets_offline_mode = False

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_financials():
    """
    Obtiene datos financieros desde Google Sheets.
    En caso de error de autenticación, devuelve datos simulados.
    """
    global sheets_offline_mode
    
    # Registrar información de las variables
    logger.info(f"Usando archivo de credenciales: {SERVICE_ACCOUNT}")
    logger.info(f"Usando ID de Google Sheet: {GOOGLE_SHEET_ID}")
    
    # Si ya sabemos que hay problemas de autenticación, ir directamente al modo fallback
    if sheets_offline_mode:
        logger.warning("Usando datos financieros de respaldo (modo offline)")
        return _get_fallback_financial_data()
    
    try:
        # Verificar que tenemos las credenciales y el ID de la hoja
        if not SERVICE_ACCOUNT or not os.path.exists(SERVICE_ACCOUNT):
            logger.error(f"Archivo de credenciales no encontrado: {SERVICE_ACCOUNT}")
            sheets_offline_mode = True
            return _get_fallback_financial_data()
            
        if not GOOGLE_SHEET_ID:
            logger.error("ID de Google Sheet no configurado")
            sheets_offline_mode = True
            return _get_fallback_financial_data()
            
        # Intentar autenticar y obtener datos
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT, scopes=scope)
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Obtener la primera hoja (asumiendo que contiene los datos financieros)
        worksheet = sheet.get_worksheet(0)
        
        # Obtener todos los datos y convertir a DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Registrar éxito
        logger.info("Datos financieros obtenidos exitosamente desde Google Sheets")
        
        return df
        
    except Exception as e:
        # Registrar el error
        logger.error(f"Error al obtener datos financieros: {str(e)}")
        
        # Marcar que estamos en modo offline para futuros intentos
        sheets_offline_mode = True
        
        # Devolver datos de respaldo
        return _get_fallback_financial_data()

def _get_fallback_financial_data():
    """
    Genera datos financieros de respaldo en caso de error de conectividad o autenticación.
    """
    # Datos simulados para el caso en que no podamos acceder a Google Sheets
    data = {
        'Mes': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
        'Ingresos': [5000, 5200, 5300, 5400, 5500, 5600, 
                     5700, 5800, 5900, 6000, 6100, 6200],
        'Gastos': [4000, 4100, 4200, 4300, 4400, 4500, 
                   4600, 4700, 4800, 4900, 5000, 5100],
        'Beneficio': [1000, 1100, 1100, 1100, 1100, 1100, 
                      1100, 1100, 1100, 1100, 1100, 1100]
    }
    return pd.DataFrame(data)

# Función para probar la conectividad a Google Sheets (útil para diagnóstico)
def test_sheets_connection():
    """
    Prueba la conexión a Google Sheets y devuelve un mensaje de diagnóstico.
    """
    try:
        # Verificar credenciales
        if not SERVICE_ACCOUNT or not os.path.exists(SERVICE_ACCOUNT):
            return {
                "success": False,
                "message": f"Archivo de credenciales no encontrado: {SERVICE_ACCOUNT}",
                "details": None
            }
            
        if not GOOGLE_SHEET_ID:
            return {
                "success": False,
                "message": "ID de Google Sheet no configurado",
                "details": None
            }
            
        # Intentar autenticar
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT, scopes=scope)
        
        client = gspread.authorize(credentials)
        
        # Intentar abrir la hoja
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Si llegamos aquí, la conexión fue exitosa
        return {
            "success": True,
            "message": "Conexión a Google Sheets exitosa",
            "details": {
                "sheet_title": sheet.title,
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
            }
        }
        
    except Exception as e:
        # Registrar y devolver el error
        return {
            "success": False,
            "message": f"Error al conectar con Google Sheets: {str(e)}",
            "details": {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }

# Función para resetear el modo offline (útil para diagnóstico)
def reset_offline_mode():
    """
    Resetea el modo offline para intentar conexiones nuevamente.
    """
    global sheets_offline_mode
    sheets_offline_mode = False
    # Limpiar también la caché de streamlit para la función get_financials
    get_financials.clear()
    return True