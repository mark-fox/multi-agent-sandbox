import os
import chromadb
from chromadb.utils import embedding_functions

# Setup Chroma
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
os.makedirs(CHROMA_DIR, exist_ok=True)

# Use a lightweight embedding model
embedding_func = embedding_functions.DefaultEmbeddingFunction()
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

def get_collection(agent_id: int):
    return chroma_client.get_or_create_collection(
        name=f"agent_{agent_id}_memories",
        embedding_function=embedding_func
    )

def add_memory(agent_id: int, text: str):
    """Add a memory chunk for this agent."""
    coll = get_collection(agent_id)
    doc_id = f"{agent_id}_{len(coll.get()['ids']) + 1}"
    coll.add(documents=[text], ids=[doc_id])

def recall_memories(agent_id: int, query: str, n_results: int = 3) -> list[str]:
    """Retrieve top relevant memories for this agent."""
    coll = get_collection(agent_id)
    if len(coll.get()['ids']) == 0:
        return []
    res = coll.query(query_texts=[query], n_results=n_results)
    return res["documents"][0]

def wipe_agent_memories(agent_id: int):
    """Delete the Chroma collection for a given agent, if it exists."""
    name = f"agent_{agent_id}_memories"
    try:
        chroma_client.delete_collection(name=name)
    except Exception:
        # If it doesn't exist yet, ignore
        pass
