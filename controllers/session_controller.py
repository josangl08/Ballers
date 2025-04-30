# controllers/session_controller.py
# Importar directamente desde nuestro controlador unificado en lugar de calendar_manager
from controllers.calendar_controller import create_calendar_event, update_calendar_event, delete_calendar_event
from models.session_model import Session, SessionStatus
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from controllers.db_controller import SessionLocal
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_session(db: DBSession, coach_id: int, player_id: int, start_time: datetime, end_time: datetime, notes: str = ""):
    try:
        # No creamos el evento de calendario aquí para evitar errores de límite de tasa
        # Los eventos se sincronizarán más tarde con sync_db_to_calendar
        
        new_session = Session(
            coach_id=coach_id,
            player_id=player_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            calendar_event_id=None,  # Inicialmente sin ID de evento
            status=SessionStatus.SCHEDULED,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    except Exception as e:
        db.rollback()
        logger.error(f"Error creando sesión: {e}")
        return None

def update_session(db: DBSession, session_id: int, start_time: datetime = None, end_time: datetime = None, status: SessionStatus = None, notes: str = None):
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        # Actualizar los campos de la sesión en la base de datos
        if start_time:
            session.start_time = start_time
        if end_time:
            session.end_time = end_time
        if status:
            session.status = status
        if notes is not None:
            session.notes = notes

        # Solo intentamos actualizar el calendario si ya tiene un ID de evento
        # De lo contrario, se sincronizará más tarde con sync_db_to_calendar
        if session.calendar_event_id:
            try:
                # Creamos un resumen descriptivo para el evento
                summary = f"Sesión: Coach {session.coach_id} - Jugador {session.player_id}"
                description = session.notes or "Sesión de entrenamiento"
                
                update_calendar_event(
                    event_id=session.calendar_event_id,
                    summary=summary,
                    description=description,
                    start_datetime=session.start_time,
                    end_datetime=session.end_time
                )
            except Exception as calendar_error:
                # Si hay un error con el calendario, lo registramos pero permitimos 
                # que la actualización de la base de datos continúe
                logger.error(f"Error actualizando evento en calendario: {calendar_error}")

        db.commit()
        db.refresh(session)
        return session

    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando sesión: {e}")
        return None

def delete_session(db: DBSession, session_id: int):
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        # Solo intentamos eliminar del calendario si ya tiene un ID de evento
        if session.calendar_event_id:
            try:
                delete_calendar_event(session.calendar_event_id)
            except Exception as calendar_error:
                # Si hay un error con el calendario, lo registramos pero permitimos 
                # que la eliminación de la base de datos continúe
                logger.error(f"Error eliminando evento del calendario: {calendar_error}")

        db.delete(session)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando sesión: {e}")
        return False

# controllers/session_controller.py (añade debajo de las otras funciones)

def get_sessions_by_player_id(player_id):
    """
    Obtiene todas las sesiones de un jugador.
    """
    try:
        with SessionLocal() as session:
            sessions = session.query(Session).filter(Session.player_id == player_id).all()
            return sessions
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener sesiones para el jugador: {e}")
        return None

def get_sessions_by_coach_id(coach_id):
    """
    Obtiene todas las sesiones de un entrenador.
    """
    try:
        with SessionLocal() as session:
            sessions = session.query(Session).filter(Session.coach_id == coach_id).all()
            return sessions
    except SQLAlchemyError as e:
        logger.error(f"Error al obtener sesiones para el entrenador: {e}")
        return None