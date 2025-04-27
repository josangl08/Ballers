# controllers/session_controller.py
from common.calendar_manager import create_calendar_event, update_calendar_event, delete_calendar_event
from models.session_model import Session, SessionStatus
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError
from controllers.db_controller import SessionLocal
from datetime import datetime

def create_session(db: DBSession, coach_id: int, player_id: int, start_time: datetime, end_time: datetime, notes: str = ""):
    try:
        calendar_event = create_calendar_event(start_time, end_time, notes)
        event_id = calendar_event['id']

        new_session = Session(
            coach_id=coach_id,
            player_id=player_id,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
            calendar_event_id=event_id,
            status=SessionStatus.SCHEDULED,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    except Exception as e:
        db.rollback()
        print(f"Error creando sesión: {e}")
        return None

def update_session(db: DBSession, session_id: int, start_time: datetime = None, end_time: datetime = None, status: SessionStatus = None, notes: str = None):
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        if session.calendar_event_id:
            update_calendar_event(session.calendar_event_id, start_time, end_time, notes)

        if start_time:
            session.start_time = start_time
        if end_time:
            session.end_time = end_time
        if status:
            session.status = status
        if notes is not None:
            session.notes = notes

        db.commit()
        db.refresh(session)
        return session

    except Exception as e:
        db.rollback()
        print(f"Error actualizando sesión: {e}")
        return None

def delete_session(db: DBSession, session_id: int):
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            return None

        if session.calendar_event_id:
            delete_calendar_event(session.calendar_event_id)

        db.delete(session)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error eliminando sesión: {e}")
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
        print(f"Error al obtener sesiones para el jugador: {e}")
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
        print(f"Error al obtener sesiones para el entrenador: {e}")
        return None
