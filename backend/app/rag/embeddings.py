import httpx
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_MODEL_EMBEDDING", "mistral")

def get_embedding(text: str) -> list[float]:
    response = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBEDDING_MODEL, "prompt": text},
        timeout=60.0
    )
    response.raise_for_status()
    return response.json()["embedding"]
