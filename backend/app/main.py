from fastapi import FastAPI
from app.db import init_db
from app.routers import rooms, agents, messages, simulate
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Multi-Agent Sandbox API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json"
)

# Allow the React dev server later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(rooms.router)
app.include_router(agents.router)
app.include_router(messages.router)   
app.include_router(simulate.router)   
