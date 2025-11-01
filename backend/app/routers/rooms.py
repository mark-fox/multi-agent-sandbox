from fastapi import APIRouter
from sqlmodel import Session, select
from app.db import engine
from app.models import Room, RoomCreate

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
