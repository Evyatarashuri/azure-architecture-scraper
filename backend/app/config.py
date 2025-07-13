# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Config:

#     # ChromaDB configuration
#     CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
#     CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "default_collection")

#     # Celery configuration
#     CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
#     CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

#     # Ollama configuration
#     OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
#     OLLAMA_MODEL_EMBEDDING = os.getenv("OLLAMA_MODEL_EMBEDDING", "nomic-embed-text")
#     OLLAMA_MODEL_CHAT = os.getenv("OLLAMA_MODEL_CHAT", "mistral")

#     # MongoDB configuration
#     MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
#     MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "scraper_db")