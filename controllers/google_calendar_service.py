# controllers/google_calendar_service.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Cargar credenciales desde archivo JSON
def get_calendar_service():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")  # Ruta al JSON de credenciales

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

def create_event(summary, description, start_datetime, end_datetime, calendar_id):
    service = get_calendar_service()

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Europe/Madrid',
        },
    }

    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return event.get('id')  # Retorna el ID del evento creado

def update_event(event_id, summary, description, start_datetime, end_datetime, calendar_id):
    service = get_calendar_service()

    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    event['summary'] = summary
    event['description'] = description
    event['start']['dateTime'] = start_datetime
    event['end']['dateTime'] = end_datetime

    updated_event = service.events().update(calendarId=calendar_id, eventId=event['id'], body=event).execute()
    return updated_event

def delete_event(event_id, calendar_id):
    service = get_calendar_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
