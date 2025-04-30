# controllers/session_controller.py
from common.calendar_manager import create_calendar_event, update_calendar_event, delete_calendar_event
from models.session_model import Session, SessionStatus
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from controllers.db_controller import get_session_local  # Importar la función, no la variable
from datetime import datetime
import logging

# Obtener el sessionmaker
SessionLocal = get_session_local()  # Crear la variable SessionLocal aquí

# Configuración de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_session(db: DBSession, coach_id: int, player_id: int, start_time: datetime, end_time: datetime, notes: str = ""):
    try:
        # Crear la sesión en la base de datos
        new_session = Session(
            coach_id=coach_id,
            player_id=player_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            calendar_event_id=None,  # Siempre NULL inicialmente (modo offline)
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

        # Si existe un evento de calendario, lo marcamos como 'pendiente de actualizar'
        # en lugar de intentar actualizarlo ahora
        if session.calendar_event_id:
            # Aquí podríamos añadir un campo en la BD para marcar como "pendiente de actualizar"
            # Por ahora, simplemente mostramos un log
            logger.info(f"Sesión {session_id} actualizada en BD, pendiente de sincronizar con Calendar")

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

        # Si existe un evento de calendario, lo marcamos para eliminación
        if session.calendar_event_id:
            try:
                # En modo offline, simplemente llamamos a la función que no hace nada real
                delete_calendar_event(session.calendar_event_id)
                logger.info(f"Evento {session.calendar_event_id} marcado para eliminación (modo offline)")
            except Exception as calendar_error:
                logger.error(f"Error al marcar evento para eliminación: {calendar_error}")

        db.delete(session)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando sesión: {e}")
        return False

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