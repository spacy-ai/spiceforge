# app/api/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.core.dependencies import get_db
from app.models.chat import ChatMessage
from app.models.circuit import Circuit

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessageCreate(BaseModel):
    circuit_id: int
    role: str  # 'user' or 'assistant'
    content: str
    message_type: str | None = None
    result: dict | None = None

class ChatMessageResponse(BaseModel):
    id: int
    circuit_id: int
    role: str
    content: str
    message_type: str | None
    result: dict | None
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/messages", response_model=ChatMessageResponse)
def save_chat_message(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
):
    """Save a chat message to the database."""
    # Verify circuit exists
    circuit = db.query(Circuit).filter(Circuit.id == message.circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    
    db_message = ChatMessage(
        circuit_id=message.circuit_id,
        role=message.role,
        content=message.content,
        message_type=message.message_type,
        result=message.result,
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

@router.get("/messages/{circuit_id}", response_model=List[ChatMessageResponse])
def get_chat_messages(
    circuit_id: int,
    db: Session = Depends(get_db),
):
    """Get all chat messages for a circuit."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.circuit_id == circuit_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return messages

@router.delete("/messages/{circuit_id}")
def clear_chat_messages(
    circuit_id: int,
    db: Session = Depends(get_db),
):
    """Clear all chat messages for a circuit."""
    db.query(ChatMessage).filter(
        ChatMessage.circuit_id == circuit_id
    ).delete()
    db.commit()
    
    return {"status": "cleared", "circuit_id": circuit_id}