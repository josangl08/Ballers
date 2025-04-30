# common/services/session_service.py
from controllers.session_controller import create_session, update_session, delete_session
from controllers.db_controller import get_session_local
from models.session_model import SessionStatus
from datetime import datetime

# Obtener el sessionmaker
SessionLocal = get_session_local()

class SessionService:
    """
    Servicio para gestionar sesiones entre entrenadores y jugadores.
    Implementa el patrón de diseño Facade para simplificar el uso del controlador.
    """
    
    @staticmethod
    def create(coach_id: int, player_id: int, start_time: datetime, end_time: datetime, notes: str = ""):
        """
        Crea una nueva sesión.
        """
        with SessionLocal() as db:
            return create_session(db, coach_id, player_id, start_time, end_time, notes)
    
    @staticmethod
    def update(db, session_id: int, start_time: datetime = None, end_time: datetime = None, 
               status: SessionStatus = None, notes: str = None):
        """
        Actualiza una sesión existente.
        """
        return update_session(db, session_id, start_time, end_time, status, notes)
    
    @staticmethod
    def delete(db, session_id: int):
        """
        Elimina una sesión.
        """
        return delete_session(db, session_id)