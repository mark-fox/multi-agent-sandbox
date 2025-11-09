import httpx
from app.config import OLLAMA_HOST, MODEL

async def generate_llm(prompt: str, system: str = "", options: dict | None = None) -> str:
    """Call the local Ollama server /api/generate."""
    payload = {
        "model": MODEL,
        "prompt": f"{system}\n\n{prompt}".strip(),
        "stream": False,
    }
    if options:
        payload["options"] = options  # e.g., {"num_predict": 60, "temperature": 0.9}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()
