# Cloud Architecture Search

This project aims to optimize cloud architecture solutions, helping organizations maximize the efficiency and scalability of their cloud infrastructures. The system uses FastAPI for the backend, FAISS for fast similarity search, Selenium for web scraping, and Ollama for AI-powered question answering.

## Overview

Organizations spend millions on cloud infrastructure but often struggle to identify the best architecture solutions for their use case. This project solves this problem by leveraging multiple technologies to provide the best possible cloud architecture based on various requirements such as performance, scalability, and cost efficiency.

## Technologies Used

- **FastAPI**  
- **Celery**  
- **Redis**  
- **MongoDB**  
- **FAISS**  
- **Selenium**  
- **Ollama**
- **TypeScript**
- **React**
- **ELK**


## Getting Started

These instructions will help you set up the project locally using Docker Compose.

### Setup Instructions

1. **Clone the repository**:

```bash
   git clone https://github.com/Evyatarashuri/azure-architecture.git
   cd azure-architecture
```

2. **Setup .env file**:

To create your local `.env` file, run one of the following commands:

On Mac/Linux:
```bash
  touch .env
```

On PowerShell:
```bash
   New-Item -Path . -Name ".env" -ItemType "File"
```

📋 **Copy the following environment variables** into your local `.env` file to configure the project properly:

```bash
# Base URL for Ollama server (used for embeddings and chat model)
OLLAMA_URL=http://ollama:11434

# Embedding model name used by Ollama
OLLAMA_MODEL_EMBEDDING=nomic-embed-text

# Chat model name used by Ollama
OLLAMA_MODEL_CHAT=mistral

# Directory path for storing FAISS index files
FAISS_INDEX_PATH=/app/faiss_store/index.faiss

# File path for storing FAISS metadata (JSON)
FAISS_METADATA_PATH=/app/faiss_store/metadata.json

# Name of the ChromaDB collection
CHROMA_COLLECTION_NAME=azure_architectures

# Path to ChromaDB persistent directory
CHROMA_DIR=/app/chroma_store

# MongoDB connection string
MONGO_URI=mongodb://mongo:27017

# MongoDB database name
DB_NAME=azure_architecture

# MongoDB collection for storing architecture links
MONGO_COLLECTION_LINKS=architecture_links

# MongoDB collection for storing architecture pages
MONGO_COLLECTION_PAGES=architecture_pages

# Celery broker URL (Redis)
CELERY_BROKER_URL=redis://redis:6379/0

# Celery result backend (Redis)
CELERY_RESULT_BACKEND=redis://redis:6379/0
```


Make sure Docker Desktop is running in the background before executing the following command.

2. **Running with Docker-compose: Build & Run**:
```bash
docker-compose up --build
```

System Requirements
In order to run the endpoints, Make sure your machine has at least:

* 12 CPU cores
* 8 GB RAM available

Running on lower specs may lead to failures or long processing times.

3. **API Endpoints (Use with Postman)**:

1. This endpoint triggers all scraping tasks and runs embeddings:
```bash
GET http://localhost:8000/scrape-all
```
What it does:

* Scrapes all architecture links from the Microsoft Azure Architecture Center.

* Scrapes each architecture's content.

* Embeds the content into FAISS for semantic search.

2. This endpoint allows you to ask a question and get an answer based on the indexed architectures:
```bash
POST http://localhost:8000/query
```
Body example (JSON):
```bash
{
  "question": "What is the best architecture for high-performance applications in Azure?"
}
```
Check out [`example-questions.md`](/docs/example-questions.md) 


> Note: Ollama runs inside a Docker container, and all models will be automatically downloaded on first run.
No manual installation is needed on your local machine.

## Technical Decisions - in building

For a deeper look into architectural decisions, trade-offs, and ideas for scaling or productionizing the app, check out the  
[DECISIONS.md](/docs/DECISIONS.md)

---

## UI & Tooling Previews

### Docker Desktop – Resource Usage
![Docker Desktop](docs/screenshots/Docker-Desktop.png)

### MongoDB Compass – Stored JSON data
![MongoDB Compass](docs/screenshots/MongoDB-compass.png)

### Postman – Model Response Example
![Postman Model Response](docs/screenshots/postman-model-response.png)

---
