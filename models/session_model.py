from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .user_model import Base

class SessionStatus(enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELED  = "canceled"

class Session(Base):
    __tablename__ = "sessions"

    id          = Column(Integer, primary_key=True)
    coach_id    = Column(Integer, ForeignKey("coaches.coach_id"), nullable=False)
    player_id   = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    start_time  = Column(DateTime, default=datetime.utcnow)
    end_time    = Column(DateTime)
    status      = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)

    # Relaciones
    coach       = relationship("Coach", back_populates="sessions")
    player      = relationship("Player", back_populates="sessions")