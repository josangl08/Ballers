# controllers/session_controller.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.session_model import Session, SessionStatus, Base
from controllers.calendar_controller import get_calendar_service
from datetime import datetime
import os

from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionDB = sessionmaker(bind=engine)
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")

# Crear tablas si no existen
def init_session_db():
    Base.metadata.create_all(engine)


def create_session(player_id, coach_id, start_time, end_time):
    """
    Inserta en la DB y crea el evento en Google Calendar.
    """
    # 1) Guardar en DB
    session = SessionDB()
    new = Session(
        player_id=player_id,
        coach_id=coach_id,
        start_time=start_time,
        end_time=end_time,
        status=SessionStatus.SCHEDULED
    )
    session.add(new)
    session.commit()
    session.refresh(new)

    # 2) Crear evento en Calendar
    service = get_calendar_service()
    event = {
        'summary': f'Sesión p{player_id} - c{coach_id}',
        'start': {'dateTime': start_time.isoformat()},
        'end': {'dateTime': end_time.isoformat()},
        'attendees': []
    }
    created = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event
    ).execute()
    return new, created.get('id')


def update_session(session_id, **kwargs):
    """
    Actualiza la sesión en DB y en Google Calendar.
    kwargs puede incluir start_time, end_time, status.
    """
    session = SessionDB()
    sess = session.query(Session).filter_by(id=session_id).first()
    if not sess:
        return None
    # Actualizar DB
    for k, v in kwargs.items():
        setattr(sess, k, v)
    session.commit()

    # Actualizar evento Calendar
    if hasattr(sess, 'calendar_event_id'):
        service = get_calendar_service()
        event = service.events().get(
            calendarId=CALENDAR_ID,
            eventId=sess.calendar_event_id
        ).execute()
        # Modificar campos
        if 'start_time' in kwargs:
            event['start']['dateTime'] = kwargs['start_time'].isoformat()
        if 'end_time' in kwargs:
            event['end']['dateTime'] = kwargs['end_time'].isoformat()
        service.events().update(
            calendarId=CALENDAR_ID,
            eventId=sess.calendar_event_id,
            body=event
        ).execute()
    return sess


def delete_session(session_id):
    """
    Borra la sesión de la DB y de Google Calendar.
    """
    session = SessionDB()
    sess = session.query(Session).filter_by(id=session_id).first()
    if not sess:
        return False
    # Borrar evento Calendar
    if hasattr(sess, 'calendar_event_id'):
        service = get_calendar_service()
        try:
            service.events().delete(
                calendarId=CALENDAR_ID,
                eventId=sess.calendar_event_id
            ).execute()
        except Exception:
            pass
    # Borrar DB
    session.delete(sess)
    session.commit()
    return True