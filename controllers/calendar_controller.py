# controllers/calendar_controller.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import streamlit as st

# Carga de credenciales desde .env
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")  # ID del calendario compartido

@st.cache_resource
def get_calendar_service():
    """
    Crea y devuelve el servicio de Google Calendar autenticado.
    """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    return service

@st.cache_data
def list_sessions_for_player(player_email):
    """
    Recupera eventos del calendario para un jugador específico (por email).
    """
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        q=player_email,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

@st.cache_data
def list_sessions_for_coach(coach_email):
    """
    Recupera eventos del calendario para un coach específico (por email).
    """
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        q=coach_email,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])