from fastapi import APIRouter, Body
from sqlmodel import Session, select
from app.db import engine
from app.models import Message

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("/{room_id}")
def list_messages(room_id: int):
    with Session(engine) as session:
        stmt = select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
        return session.exec(stmt).all()

@router.post("/human/{room_id}")
def human_message(room_id: int, data: dict = Body(...)):
    """
    Add a human-authored message to a room.
    Expected body: { "content": "your message here" }
    """
    content = data.get("content", "").strip()
    if not content:
        return {"error": "Message content cannot be empty."}

    with Session(engine) as session:
        msg = Message(room_id=room_id, agent_id=None, content=f"🧍 Human: {content}")
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg