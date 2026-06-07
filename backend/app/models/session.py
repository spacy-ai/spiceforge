from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CircuitSession(Base):
    __tablename__ = "circuit_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=True, index=True)
    context = Column(Text, default="")
    latest_blueprint_json = Column(Text, nullable=True)
    latest_netlist = Column(Text, default="")
    simulation_history_json = Column(Text, nullable=True)
    retry_history_json = Column(Text, nullable=True)
    conversation_history_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
