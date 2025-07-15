import os
import faiss
import numpy as np
import json
from langchain_community.chat_models import ChatOllama
from langchain.schema import HumanMessage
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tasks.scrape_tasks import get_embeddings_batch
from app.logging_config import logger

router = APIRouter()

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/app/faiss_store/index.faiss")
FAISS_METADATA_PATH = os.getenv("FAISS_METADATA_PATH", "/app/faiss_store/metadata.json")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL_CHAT = os.getenv("OLLAMA_MODEL_CHAT", "mistral")


llm = ChatOllama(
    model=OLLAMA_MODEL_CHAT,
    temperature=0,
    base_url=OLLAMA_URL
)

class QueryRequest(BaseModel):
    question: str  # Question model

def load_faiss_data():
    """Load both FAISS index and metadata."""
    try:
        # Load FAISS index
        index = faiss.read_index(FAISS_INDEX_PATH)
        # Load metadata
        with open(FAISS_METADATA_PATH, "r") as f:
            metadata = json.load(f)
        logger.info(f"Loaded FAISS index and metadata: {index.ntotal} vectors, {len(metadata)} entries.")
        return index, metadata
    except Exception as e:
        logger.error(f"Failed to load FAISS index or metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to load FAISS index or metadata.")

@router.post("/")
async def query_architectures(req: QueryRequest):
    """Query the FAISS index for the best match and use Ollama to get the answer."""
    index, metadata = load_faiss_data()  # Load the FAISS index and metadata

    # Get the embedding for the user's question
    query_embedding = get_embeddings_batch([req.question])[0]
    query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

    # Perform vector search
    D, I = index.search(query_embedding, k=3)

    if len(I[0]) == 0:  # If no relevant documents were found
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    # Fetch the corresponding documents from metadata
    docs = [metadata[i] for i in I[0]]

    # Prepare the context for the response
    context = "\n\n".join([doc['document'] for doc in docs])
    prompt = f"""
    Answer the following question based only on the context below.
    If the answer is not in the context, say "I don't know".

    Context:
    {context}

    Question: {req.question}
    """
    
    # Use Ollama to get the answer based on the context
    response = llm([HumanMessage(content=prompt)])

    # Return the response with the relevant sources
    return {
        "question": req.question,
        "answer": response.content,
        "sources": [{"metadata": doc["metadata"]} for doc in docs]
    }
