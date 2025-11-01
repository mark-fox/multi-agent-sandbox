# Multi-Agent Sandbox

Local multi-agent simulation using **FastAPI**, **SQLite**, and **Ollama** (Mistral).  
Each "room" hosts AI agents with defined roles and goals that take turns generating messages locally — no paid APIs required.

## Current Features
- FastAPI backend (Python 3.11)
- Local LLM via [Ollama](https://ollama.com/)
- SQLite for persistence
- Room and agent creation
- Turn-based message simulation
- Simple `/docs` Swagger UI for testing

## Quick Start
```bash
# In backend/
python -m venv .venv && .venv\Scripts\Activate
pip install -r requirements.txt  # or manually install fastapi, uvicorn, sqlmodel, httpx, python-dotenv
uvicorn app.main:app --reload --port 8000
