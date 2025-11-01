from fastapi import APIRouter
from sqlmodel import Session, select
from app.db import engine
from app.models import Agent

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/{room_id}")
def list_agents(room_id: int):
    with Session(engine) as session:
        stmt = select(Agent).where(Agent.room_id == room_id)
        return session.exec(stmt).all()

@router.post("")
def create_agent(agent: Agent):
    with Session(engine) as session:
        session.add(agent)
        session.commit()
        session.refresh(agent)
        return agent
