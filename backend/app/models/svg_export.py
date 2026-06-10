# app/models/export.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

class SvgExport(Base):
    __tablename__ = "svg_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_id = Column(String(36), unique=True, index=True, nullable=False)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=True)
    content = Column(Text, nullable=False)  # Store the actual HTML/SVG content here!
    format = Column(String(20), nullable=False)  # 'interactive' or 'standard'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON as string