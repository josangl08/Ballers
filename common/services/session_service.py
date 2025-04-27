from controllers.session_controller import create_session, update_session, delete_session
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from models.session_model import SessionStatus

class SessionService:

    @staticmethod
    def create(db: DBSession, coach_id: int, player_id: int, start_time: datetime, end_time: datetime, notes: str = ""):
        return create_session(db, coach_id, player_id, start_time, end_time, notes)

    @staticmethod
    def update(db: DBSession, session_id: int, start_time: datetime = None, end_time: datetime = None, status: SessionStatus = None, notes: str = None):
        return update_session(db, session_id, start_time, end_time, status, notes)

    @staticmethod
    def delete(db: DBSession, session_id: int):
        return delete_session(db, session_id)
