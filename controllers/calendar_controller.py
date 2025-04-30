# controllers/calendar_controller.py
import os
import time
import random
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import streamlit as st

from models.session_model import Session
from models.coach_model import Coach
from models.player_model import Player
from models.user_model import User

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de credenciales
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
if not SERVICE_ACCOUNT_FILE:
    SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# --------------------------------
# Funciones stub para modo "offline"
# --------------------------------

def create_calendar_event(summary, description, start_datetime, end_datetime, attendees=None):
    """
    Versión OFFLINE: Solo registra la operación, no intenta realmente conectarse a la API.
    """
    logger.info(f"[MODO OFFLINE] Se registraría un evento con título: {summary}")
    # Generar un ID falso para simular la creación exitosa
    fake_id = f"offline_{int(time.time())}_{random.randint(1000, 9999)}"
    return {"id": fake_id}

def update_calendar_event(event_id, summary=None, description=None, start_datetime=None, end_datetime=None, attendees=None):
    """
    Versión OFFLINE: Solo registra la operación, no intenta realmente conectarse a la API.
    """
    logger.info(f"[MODO OFFLINE] Se actualizaría el evento con ID: {event_id}")
    return {"id": event_id}

def delete_calendar_event(event_id):
    """
    Versión OFFLINE: Solo registra la operación, no intenta realmente conectarse a la API.
    """
    logger.info(f"[MODO OFFLINE] Se eliminaría el evento con ID: {event_id}")
    return True

def list_calendar_events(query=None, time_min=None, time_max=None, max_results=100):
    """
    Versión OFFLINE: Devuelve una lista vacía.
    """
    logger.info(f"[MODO OFFLINE] Se listarían eventos con filtro: {query}")
    return []

def get_calendar_event(event_id):
    """
    Versión OFFLINE: Devuelve un evento falso.
    """
    logger.info(f"[MODO OFFLINE] Se obtendría el evento con ID: {event_id}")
    return {
        "id": event_id,
        "summary": "Evento offline",
        "description": "Este es un evento simulado en modo offline",
        "start": {"dateTime": datetime.now().isoformat()},
        "end": {"dateTime": (datetime.now() + timedelta(hours=1)).isoformat()}
    }

# --------------------------------
# Funciones reales para Google Calendar (para usar en sincronización controlada)
# --------------------------------

@st.cache_resource
def get_calendar_service():
    """
    Crea y devuelve el servicio de Google Calendar autenticado.
    """
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("La variable de entorno para el archivo de credenciales no está configurada.")
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Error al crear el servicio de Google Calendar: {e}")
        raise

def _real_create_calendar_event(summary, description, start_datetime, end_datetime, attendees=None):
    """
    Versión real de creación de eventos - solo para uso interno controlado.
    """
    service = get_calendar_service()
    
    # Formato adecuado para las fechas
    if isinstance(start_datetime, str):
        start_datetime = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
    if isinstance(end_datetime, str):
        end_datetime = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
    
    # Crear el cuerpo del evento
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'Europe/Madrid',
        },
    }
    
    # Añadir asistentes si se proporcionan
    if attendees:
        event['attendees'] = attendees
    
    # Esperar un tiempo considerable entre solicitudes (5 segundos)
    time.sleep(5)
    
    # Crear el evento
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return created_event

def _real_delete_calendar_event(event_id):
    """
    Versión real de eliminación de eventos - solo para uso interno controlado.
    """
    service = get_calendar_service()
    
    # Esperar un tiempo considerable entre solicitudes (5 segundos)
    time.sleep(5)
    
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    return True

def sync_single_session(db_session, session_id):
    """
    Sincroniza una única sesión con Google Calendar.
    Devuelve True si tiene éxito, False si falla.
    """
    try:
        # Obtener la sesión
        session = db_session.query(Session).filter(Session.id == session_id).first()
        if not session:
            logger.error(f"No se encontró la sesión con ID {session_id}")
            return False
        
        # Obtener datos de coach y jugador
        coach = db_session.query(Coach).filter_by(coach_id=session.coach_id).first()
        player = db_session.query(Player).filter_by(player_id=session.player_id).first()
        
        # Si no podemos encontrar la información necesaria, fallamos
        if not coach or not player:
            logger.error(f"No se pudo encontrar información para la sesión {session.id}")
            return False
        
        # Obtener emails para asistentes (si están disponibles)
        attendees = []
        coach_user = db_session.query(User).filter_by(user_id=coach.user_id).first() if coach else None
        player_user = db_session.query(User).filter_by(user_id=player.user_id).first() if player else None
        
        if coach_user and coach_user.email:
            attendees.append({'email': coach_user.email})
        if player_user and player_user.email:
            attendees.append({'email': player_user.email})
        
        # Crear el título y descripción del evento
        coach_name = getattr(coach, 'name', None) or getattr(coach_user, 'name', f'Coach {coach.coach_id}')
        player_name = getattr(player, 'name', None) or getattr(player_user, 'name', f'Jugador {player.player_id}')
        
        summary = f"Sesión: {coach_name} - {player_name}"
        description = session.notes or "Sesión de entrenamiento"
        
        # Crear el evento en el calendario
        event = _real_create_calendar_event(
            summary=summary,
            description=description,
            start_datetime=session.start_time,
            end_datetime=session.end_time,
            attendees=attendees if attendees else None
        )
        
        # Guardar el ID del evento en la sesión
        session.calendar_event_id = event.get('id')
        db_session.commit()
        
        logger.info(f"Evento creado para sesión {session.id}: {event.get('id')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al sincronizar sesión {session_id}: {e}")
        db_session.rollback()
        return False

def sync_db_to_calendar(db_session, batch_size=1):
    """
    Sincroniza sesiones de la base de datos a Google Calendar.
    Esta es la función controlada que se llama explícitamente desde la UI.
    """
    # Obtener sesiones sin ID de evento de calendario
    pending_sessions = db_session.query(Session).filter(Session.calendar_event_id.is_(None)).all()
    total_pending = len(pending_sessions)
    
    logger.info(f"Encontradas {total_pending} sesiones pendientes de sincronizar")
    
    if total_pending == 0:
        return 0
    
    # Solo intentar sincronizar una sesión a la vez para máxima seguridad
    session = pending_sessions[0]
    result = sync_single_session(db_session, session.id)
    
    return 1 if result else 0

def sync_calendar_to_db(db_session):
    """
    Sincroniza eventos de Google Calendar a la base de datos.
    """
    # Esta función se implementará en la siguiente fase
    logger.info("La sincronización Calendar → DB aún no está implementada")
    return 0