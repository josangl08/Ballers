

from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
from datetime import datetime

# Configuración para conectarse a Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'data/credentials.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build('calendar', 'v3', credentials=credentials)

# Funciones para gestionar eventos en Google Calendar
def create_calendar_event(start_time: datetime, end_time: datetime, notes: str):
    event = {
        'summary': 'Training Session',
        'description': notes,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Madrid',  # o la que corresponda
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Madrid',
        },
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event

def update_calendar_event(event_id: str, start_time: datetime = None, end_time: datetime = None, notes: str = None):
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        if start_time:
            event['start']['dateTime'] = start_time.isoformat()
        if end_time:
            event['end']['dateTime'] = end_time.isoformat()
        if notes is not None:
            event['description'] = notes

        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event
    except Exception as e:
        print(f"Error actualizando evento de Google Calendar: {e}")
        return None

def delete_calendar_event(event_id: str):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
    except Exception as e:
        print(f"Error eliminando evento de Google Calendar: {e}")
