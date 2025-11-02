from fastapi import APIRouter
from sqlmodel import Session, select
from app.db import engine
from app.models import Room, Agent, Message
from app.llm import generate_llm
from app.memory import add_memory, recall_memories

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

        history = session.exec(
            select(Message).where(Message.room_id == room_id).order_by(Message.created_at)
        ).all()
        history_text = "\n".join([f"{m.agent_id}:{m.content}" for m in history[-12:]])

        # Recall top relevant memories for this agent
        recalled = recall_memories(next_agent.id, history_text, n_results=3)
        memory_text = "\n".join(recalled) if recalled else "No relevant past memories."

        system = f"You are {next_agent.name}, a {next_agent.role}. Your goal: {next_agent.goal}."
        prompt = (
            f"Conversation so far:\n{history_text}\n\n"
            f"Relevant past memories:\n{memory_text}\n\n"
            f"Your next reply:"
        )

        reply = await generate_llm(prompt, system=system)

        msg = Message(room_id=room_id, agent_id=next_agent.id, content=reply)
        session.add(msg)
        session.commit()
        session.refresh(msg)

        # Add new message to agent's memory
        add_memory(next_agent.id, reply)

        return msg
    
    
@router.post("/judge/{room_id}")
async def judge_turn(room_id: int):
    """Judge the most recent turn in this room."""
    with Session(engine) as session:
        room = session.get(Room, room_id)
        if not room:
            return {"error": "Room not found"}

        agents = session.exec(select(Agent).where(Agent.room_id == room_id)).all()
        if not agents:
            return {"error": "No agents in room"}

        messages = session.exec(
            select(Message)
            .where(Message.room_id == room_id)
            .order_by(Message.created_at)
        ).all()

        if len(messages) < 1:
            return {"error": "No messages yet"}

        # Context for judging (last 5 messages)
        context = "\n".join(
            [
                f"{m.agent_id}:{m.content}"
                for m in messages[-5:]
                if m.content
            ]
        )

        last_msg = messages[-1]
        last_agent = next((a for a in agents if a.id == last_msg.agent_id), None)

        system = (
            "You are a neutral judge evaluating the most recent message in a discussion.\n"
            "Your task: assess the quality, logic, or helpfulness of the last message "
            "in the context of the conversation.\n"
            "Output in one concise paragraph followed by a score from 1–10."
        )

        prompt = (
            f"Conversation so far:\n{context}\n\n"
            f"Evaluate the last message ({last_agent.name if last_agent else 'Unknown'}):"
        )

        feedback = await generate_llm(prompt, system=system)

        msg = Message(room_id=room_id, agent_id=None, content=f"🧑‍⚖️ Judge: {feedback}")
        session.add(msg)
        session.commit()
        session.refresh(msg)
        return msg
