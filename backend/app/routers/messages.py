from fastapi import APIRouter
from sqlmodel import Session, select
from app.db import engine
from app.models import Message

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/{room_id}")
def list_messages(room_id: int):
    with Session(engine) as session:
        stmt = select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
        return session.exec(stmt).all()
