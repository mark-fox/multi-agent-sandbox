from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Room(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    scenario: str = "freeplay"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoomCreate(SQLModel):
    name: str
    scenario: str = "freeplay"
    
class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(index=True, foreign_key="room.id")
    name: str
    role: str
    goal: str

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(index=True, foreign_key="room.id")
    agent_id: Optional[int] = Field(default=None, foreign_key="agent.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
