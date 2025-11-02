from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select
from datetime import datetime
from app.db import engine
from app.models import Room, RoomCreate, Agent, Message

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.get("")
def list_rooms():
    with Session(engine) as session:
        return session.exec(select(Room)).all()

@router.post("")
def create_room(payload: RoomCreate):
    with Session(engine) as session:
        room = Room(name=payload.name, scenario=payload.scenario)
        session.add(room)
        session.commit()
        session.refresh(room)
        return room

@router.get("/{room_id}/export.md")
def export_room_markdown(room_id: int):
    """Return a Markdown transcript for the given room."""
    with Session(engine) as session:
        room = session.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        agents = session.exec(select(Agent).where(Agent.room_id == room_id)).all()
        agent_by_id = {a.id: a for a in agents}

        messages = session.exec(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
        ).all()

        created = room.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(room, "created_at") else ""
        lines = []
        lines.append(f"# Room: {room.name}")
        lines.append(f"_Scenario:_ **{room.scenario}**   ")
        if created:
            lines.append(f"_Created:_ {created}   ")
        lines.append("")
        if agents:
            lines.append("## Agents")
            for a in agents:
                lines.append(f"- **{a.name}** — {a.role}. Goal: {a.goal}")
            lines.append("")

        lines.append("## Transcript")
        if not messages:
            lines.append("_No messages yet._")
        else:
            for m in messages:
                who = agent_by_id.get(m.agent_id).name if m.agent_id in agent_by_id else "System"
                timestamp = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"**{who}** [{timestamp}]:")
                # indent message body as a blockquote to preserve formatting
                for line in (m.content or "").splitlines() or [""]:
                    lines.append(f"> {line}")
                lines.append("")  # blank line between messages

        md = "\n".join(lines)
        filename = f"{room.name.replace(' ', '_')}_transcript.md"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=md, media_type="text/markdown; charset=utf-8", headers=headers)