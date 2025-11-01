from fastapi import APIRouter
from sqlmodel import Session, select
from app.db import engine
from app.models import Room, Agent, Message
from app.llm import generate_llm

router = APIRouter(prefix="/simulate", tags=["simulate"])

SYSTEM_TEMPLATE = "You are {name}, a {role}. Your goal: {goal}. Stay concise and in-character."

@router.post("/turn/{room_id}")
async def simulate_turn(room_id: int):
    with Session(engine) as session:
        room = session.get(Room, room_id)
        if not room:
            return {"error": "Room not found"}

        agents = session.exec(select(Agent).where(Agent.room_id == room_id)).all()
        if not agents:
            return {"error": "No agents in room"}

        # Last message to decide next speaker (round-robin)
        last_msg = session.exec(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at.desc())
        ).first()

        if last_msg and last_msg.agent_id:
            try:
                last_index = next(i for i, a in enumerate(agents) if a.id == last_msg.agent_id)
            except StopIteration:
                last_index = -1
            next_agent = agents[(last_index + 1) % len(agents)]
        else:
            next_agent = agents[0]

        # Small history context
        history = session.exec(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
        ).all()
        history_text = "\n".join([f"{m.agent_id}:{m.content}" for m in history[-12:]])

        system = SYSTEM_TEMPLATE.format(name=next_agent.name, role=next_agent.role, goal=next_agent.goal)
        prompt = f"Conversation so far:\n{history_text}\n\nYour turn:"

        reply = await generate_llm(prompt, system=system)

        msg = Message(room_id=room_id, agent_id=next_agent.id, content=reply)
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg
