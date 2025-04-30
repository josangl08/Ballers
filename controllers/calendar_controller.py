# controllers/calendar_controller_unified.py
import os
import time
import random
import threading
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

# Sistema de tokens de cuota
class QuotaTokenBucket:
    """
    Implementa un sistema de token bucket para controlar la tasa de solicitudes.
    Esto asegura que no excedamos la cuota de la API de Google.
    """
    def __init__(self, tokens_per_minute=5, max_tokens=5):
        self.tokens = max_tokens
        self.max_tokens = max_tokens
        self.tokens_per_minute = tokens_per_minute
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
    def get_token(self, block=True, timeout=None):
        """
        Obtiene un token del bucket. Si no hay tokens disponibles,
        espera hasta que se repongan o hasta que se agote el tiempo de espera.
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                # Refill tokens based on elapsed time
                now = time.time()
                elapsed = now - self.last_refill
                new_tokens = int(elapsed * (self.tokens_per_minute / 60.0))
                
                if new_tokens > 0:
                    self.tokens = min(self.tokens + new_tokens, self.max_tokens)
                    self.last_refill = now
                
                # If we have tokens, consume one and return
                if self.tokens > 0:
                    self.tokens -= 1
                    return True
            
            # If we're not blocking, return False
            if not block:
                return False
                
            # Check if we've timed out
            if timeout is not None and time.time() - start_time > timeout:
                return False
                
            # Sleep for a bit before checking again
            interval = 60.0 / self.tokens_per_minute
            time.sleep(interval)

# Creamos un bucket de tokens global con límites muy conservadores
# 5 solicitudes por minuto, máximo 5 tokens
quota_bucket = QuotaTokenBucket(tokens_per_minute=5, max_tokens=5)

# Reintentos y retroceso exponencial
MAX_RETRIES = 10
INITIAL_WAIT = 5  # segundos
MAX_WAIT = 120    # máximo tiempo de espera entre intentos

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

def safe_api_call(func):
    """
    Decorador que combina el sistema de tokens con reintentos y retroceso exponencial.
    """
    def wrapper(*args, **kwargs):
        wait_time = INITIAL_WAIT
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            # Obtener un token (esperar si es necesario)
            logger.info(f"Esperando un token de cuota... (intento {attempt+1}/{MAX_RETRIES})")
            if not quota_bucket.get_token(timeout=300):  # 5 minutos máximo de espera
                logger.error("Tiempo de espera agotado esperando tokens de cuota")
                raise Exception("Tiempo de espera agotado esperando tokens de cuota")
                
            logger.info(f"Token obtenido. Ejecutando solicitud a la API... (intento {attempt+1}/{MAX_RETRIES})")
            
            try:
                # Ejecutar la función
                return func(*args, **kwargs)
                
            except HttpError as e:
                last_error = e
                if e.resp.status == 403 and "Rate Limit Exceeded" in str(e):
                    if attempt == MAX_RETRIES - 1:  # Si es el último intento
                        logger.error(f"Se alcanzó el máximo de reintentos ({MAX_RETRIES}). Error: {e}")
                        raise
                    
                    # Añadir jitter para evitar sincronización
                    jitter = random.uniform(0, 5)
                    sleep_time = min(wait_time + jitter, MAX_WAIT)
                    
                    logger.warning(f"Rate limit exceeded. Intento {attempt+1}/{MAX_RETRIES}. Reintentando en {sleep_time:.2f} segundos...")
                    time.sleep(sleep_time)
                    
                    # Incrementar el tiempo de espera exponencialmente
                    wait_time = min(wait_time * 2, MAX_WAIT)
                else:
                    # Si es otro tipo de error, lo registramos y lanzamos
                    logger.error(f"Error en la solicitud a Google Calendar: {e}")
                    raise
            except Exception as e:
                last_error = e
                logger.error(f"Error inesperado: {e}")
                raise
                
        # Si llegamos aquí, todos los intentos fallaron
        if last_error:
            raise last_error
        else:
            raise Exception("Error desconocido durante la llamada a la API")
            
    return wrapper

@safe_api_call
def create_calendar_event(summary, description, start_datetime, end_datetime, attendees=None):
    """
    Crea un evento en Google Calendar con manejo de límites de tasa.
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
    
    logger.info(f"Creando evento: {summary}")
    # Crear el evento
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    logger.info(f"Evento creado con ID: {created_event.get('id')}")
    return created_event

@safe_api_call
def update_calendar_event(event_id, summary=None, description=None, start_datetime=None, end_datetime=None, attendees=None):
    """
    Actualiza un evento existente en Google Calendar con manejo de límites de tasa.
    """
    service = get_calendar_service()
    
    logger.info(f"Obteniendo evento con ID: {event_id}")
    # Obtener el evento actual
    event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    
    # Actualizar los campos proporcionados
    if summary:
        event['summary'] = summary
    if description:
        event['description'] = description
    if start_datetime:
        if isinstance(start_datetime, str):
            start_datetime = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        event['start']['dateTime'] = start_datetime.isoformat()
    if end_datetime:
        if isinstance(end_datetime, str):
            end_datetime = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        event['end']['dateTime'] = end_datetime.isoformat()
    if attendees:
        event['attendees'] = attendees
    
    logger.info(f"Actualizando evento: {event.get('summary', 'Sin título')}")
    # Actualizar el evento
    updated_event = service.events().update(calendarId=CALENDAR_ID, eventId=event_id, body=event).execute()
    logger.info(f"Evento actualizado: {updated_event.get('id')}")
    return updated_event

@safe_api_call
def delete_calendar_event(event_id):
    """
    Elimina un evento de Google Calendar con manejo de límites de tasa.
    """
    service = get_calendar_service()
    logger.info(f"Eliminando evento con ID: {event_id}")
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    logger.info(f"Evento eliminado: {event_id}")
    return True

@safe_api_call
def list_calendar_events(query=None, time_min=None, time_max=None, max_results=100):
    """
    Lista eventos del calendario con filtros opcionales y manejo de límites de tasa.
    """
    service = get_calendar_service()
    
    # Preparar parámetros para la solicitud
    params = {
        'calendarId': CALENDAR_ID,
        'singleEvents': True,
        'orderBy': 'startTime',
        'maxResults': max_results
    }
    
    if query:
        params['q'] = query
    if time_min:
        if isinstance(time_min, datetime):
            time_min = time_min.isoformat() + 'Z'
        params['timeMin'] = time_min
    if time_max:
        if isinstance(time_max, datetime):
            time_max = time_max.isoformat() + 'Z'
        params['timeMax'] = time_max
    
    logger.info(f"Listando eventos con parámetros: {params}")
    # Hacer la solicitud
    events_result = service.events().list(**params).execute()
    logger.info(f"Se encontraron {len(events_result.get('items', []))} eventos")
    return events_result.get('items', [])

@safe_api_call
def get_calendar_event(event_id):
    """
    Obtiene un evento específico por su ID con manejo de límites de tasa.
    """
    service = get_calendar_service()
    logger.info(f"Obteniendo evento con ID: {event_id}")
    event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    return event

def sync_db_to_calendar(db_session, batch_size=1):
    """
    Sincroniza sesiones de la base de datos a Google Calendar.
    Procesa las sesiones en lotes pequeños para evitar límites de tasa.
    Devuelve el número de eventos nuevos creados.
    """
    # Obtener sesiones sin ID de evento de calendario
    pending_sessions = db_session.query(Session).filter(Session.calendar_event_id.is_(None)).all()
    total_pending = len(pending_sessions)
    
    logger.info(f"Encontradas {total_pending} sesiones pendientes de sincronizar")
    
    events_created = 0
    
    # Procesar en lotes pequeños
    for i in range(0, total_pending, batch_size):
        batch = pending_sessions[i:i+batch_size]
        logger.info(f"Procesando lote {i//batch_size + 1}/{(total_pending + batch_size - 1)//batch_size}")
        
        for session in batch:
            try:
                # Obtener datos de coach y jugador
                coach = db_session.query(Coach).filter_by(coach_id=session.coach_id).first()
                player = db_session.query(Player).filter_by(player_id=session.player_id).first()
                
                # Si no podemos encontrar la información necesaria, continuamos con la siguiente sesión
                if not coach or not player:
                    logger.warning(f"No se pudo encontrar información para la sesión {session.id}")
                    continue
                
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
                event = create_calendar_event(
                    summary=summary,
                    description=description,
                    start_datetime=session.start_time,
                    end_datetime=session.end_time,
                    attendees=attendees if attendees else None
                )
                
                # Guardar el ID del evento en la sesión
                session.calendar_event_id = event.get('id')
                db_session.commit()
                
                events_created += 1
                logger.info(f"Evento creado para sesión {session.id}: {event.get('id')}")
                
            except Exception as e:
                logger.error(f"Error al sincronizar sesión {session.id}: {e}")
                db_session.rollback()
                
                # Si hay un error, hacemos una pausa más larga antes de continuar
                logger.info(f"Esperando 30 segundos antes de continuar...")
                time.sleep(30)
    
    return events_created

def sync_calendar_to_db(db_session):
    """
    Sincroniza eventos de Google Calendar a la base de datos.
    Devuelve el número de sesiones actualizadas o creadas.
    """
    # Implementar lógica para sincronizar desde el calendario hacia la base de datos
    # Esta sería la segunda fase de tu proyecto
    logger.info("La sincronización Calendar -> DB aún no está implementada")
    return 0