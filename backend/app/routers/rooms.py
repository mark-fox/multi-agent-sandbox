from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from sqlmodel import Session, select
from datetime import datetime
from app.db import engine
from app.models import Room, RoomCreate, Agent, Message
from app.scenarios import SCENARIOS
from app.memory import wipe_agent_memories

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
    
@router.post("/build/{scenario_key}")
def build_scenario_room(scenario_key: str):
    """Create a new room with predefined agents from a scenario template."""
    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    with Session(engine) as session:
        room = Room(name=scenario_key.replace("_", " ").title(), scenario=scenario_key)
        session.add(room)
        session.commit()
        session.refresh(room)

        for a in scenario["agents"]:
            agent = Agent(room_id=room.id, name=a["name"], role=a["role"], goal=a["goal"])
            session.add(agent)
        session.commit()

        return {
            "room": room,
            "agents": session.exec(select(Agent).where(Agent.room_id == room.id)).all(),
            "description": scenario["description"],
        }
    
@router.post("/{room_id}/reset")
def reset_room(room_id: int, wipe: str = Query("messages", enum=["messages", "all"])):
    """
    Reset a room.
    - wipe=messages (default): delete all messages
    - wipe=all: delete all messages AND wipe agent memories (Chroma)
    """
    with Session(engine) as session:
        room = session.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Delete all messages for this room
        msgs = session.exec(select(Message).where(Message.room_id == room_id)).all()
        for m in msgs:
            session.delete(m)
        session.commit()

        wiped = {"messages": len(msgs), "memories": 0}

        if wipe == "all":
            agents = session.exec(select(Agent).where(Agent.room_id == room_id)).all()
            for a in agents:
                wipe_agent_memories(a.id)
                wiped["memories"] += 1

        return {"ok": True, "room_id": room_id, "wiped": wiped}
    
@router.delete("/{room_id}")
def delete_room(room_id: int):
    """
    Delete a room and EVERYTHING associated with it:
    - all messages in the room
    - all agents in the room
    - each agent's Chroma memories
    - the room itself
    """
    with Session(engine) as session:
        room = session.get(Room, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # Delete messages
        msgs = session.exec(select(Message).where(Message.room_id == room_id)).all()
        for m in msgs:
            session.delete(m)

        # Wipe memories + delete agents
        agents = session.exec(select(Agent).where(Agent.room_id == room_id)).all()
        for a in agents:
            wipe_agent_memories(a.id)
            session.delete(a)

        # Finally delete the room
        session.delete(room)
        session.commit()

        return {"ok": True, "room_id": room_id, "deleted": {"messages": len(msgs), "agents": len(agents)}}