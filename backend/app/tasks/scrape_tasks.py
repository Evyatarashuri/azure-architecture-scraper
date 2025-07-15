from celery import Celery
import os
from dotenv import load_dotenv
import httpx
import uuid
import numpy as np
import json
import faiss
from app.logging_config import logger
from app.scrape.scrape_links_and_data import scrape_architecture_page, scrape_links

from app.db.mongo import (
    insert_architecture_links,
    insert_architecture_page_data,
    get_links_collection,
    get_pages_collection
)

load_dotenv()

celery_app = Celery(
    "scraper",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL_EMBEDDING = os.getenv("OLLAMA_MODEL_EMBEDDING", "nomic-embed-text")


FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH" ,"/app/faiss_store/index.faiss")
FAISS_METADATA_PATH = os.getenv("FAISS_METADATA_PATH" ,"/app/faiss_store/metadata.json")


# fetch links task
@celery_app.task(name="fetch_links_task")
def fetch_links_task():
    links_collection = get_links_collection()

    logger.info(f"Found {links_collection.count_documents({})} links in MongoDB")
    logger.info("Fetching all architecture links...")

    existing_count = links_collection.count_documents({})
    if existing_count >= 352:
        logger.info(f"Found {existing_count} links in MongoDB — skipping scraping.")
        return

    logger.info("Scraping links with Selenium...")
    all_links = []
    skip = 0

    while True:
        links = scrape_links(skip)
        if not links:
            break
        insert_architecture_links(links)
        all_links.extend(links)
        skip += 6

    logger.info(f"Total {len(set(all_links))} unique links inserted to MongoDB")


# scrape each page task
@celery_app.task(name="scrape_each_page_task")
def scrape_each_page_task(_=None):
    links_collection = get_links_collection()
    pages_collection = get_pages_collection()

    logger.info("Loading links from MongoDB and scraping each page...")

    existing_count = pages_collection.count_documents({})
    logger.info(f"Found {existing_count} pages in MongoDB")

    if existing_count >= 352:
        logger.info(f"Found {existing_count} pages in MongoDB — skipping scraping.")
        return

    urls = [doc["url"] for doc in links_collection.find({})]
    total = len(urls)
    logger.info(f"🔢 Total URLs to scrape: {total}")

    for i, url in enumerate(urls, start=1):
        try:
            if insert_architecture_page_data({"url": url}, check_only=True):
                logger.info(f"[{i}/{total}] Skipping {url} - already in MongoDB.")
                continue

            data = scrape_architecture_page(url)
            insert_architecture_page_data(data)

            logger.info(f"[{i}/{total}] Saved to MongoDB: {url}")

        except Exception as e:
            logger.error(f"[{i}/{total}] Failed for {url}: {e}")


# Function to get embeddings from Ollama
def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    logger.info("Sending texts to Ollama for embedding...")

    response = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": OLLAMA_MODEL_EMBEDDING, "input": texts},
        timeout=120.0
    )

    print(f"📬 Received response from Ollama: {response.status_code}")

    response.raise_for_status()

    data = response.json()
    if "embeddings" in data:
        logger.info(f"Successfully received embeddings with {len(data['embeddings'])} entries.")
    else:
        logger.error("No embeddings found in the response.")

    return data["embeddings"]


def chunk_text(text: str, max_tokens: int = 8000) -> list[str]:
    lines = text.split("\n")
    chunks = []
    current_chunk = ""
    for line in lines:
        if len(current_chunk) + len(line) < max_tokens:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


@celery_app.task(name="embed_all_pages_direct")
def embed_all_pages_direct(_=None):
    dimension = 768
    faiss_store_dir = os.path.dirname(FAISS_INDEX_PATH)

    os.makedirs(faiss_store_dir, exist_ok=True)
    logger.info(f"Faiss store directory: {faiss_store_dir}")

    index = faiss.IndexFlatL2(dimension)
    metadata = []
    processed_doc_ids = set()

    if os.path.exists(FAISS_INDEX_PATH):
        try:
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_METADATA_PATH, "r") as f:
                metadata = json.load(f)
            processed_doc_ids = {entry.get("doc_id") for entry in metadata}
            logger.info(f"Loaded existing index with {index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load Faiss index or metadata: {e}")
            raise

    pages_collection = get_pages_collection()
    documents = list(pages_collection.find({"_id": {"$nin": list(processed_doc_ids)}}))
    logger.info(f"Found {len(documents)} documents to embed")

    for doc_index, doc in enumerate(documents, start=1):
        doc_id = str(doc["_id"])
        logger.info(f"\nEmbedding document {doc_index} | ID: {doc_id}")

        content = f"{doc.get('title', '')}\n{' '.join(doc.get('tags', []))}\n{doc.get('content', '')}"
        chunks = chunk_text(content)

        if not chunks:
            logger.warning(f"Skipping empty document {doc_id}")
            continue

        batch_size = 10
        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            batch_ids = [f"{doc_id}-{uuid.uuid4()}" for _ in range(len(batch))]

            try:
                embeddings = get_embeddings_batch(batch)
                embeddings = np.array(embeddings, dtype=np.float32)

                if embeddings.shape[1] != dimension:
                    raise ValueError(f"Embedding dimension mismatch: expected {dimension}, got {embeddings.shape[1]}")
                if np.any(np.isnan(embeddings)) or np.any(np.isinf(embeddings)):
                    raise ValueError("NaN or inf values found in embeddings")

                metadatas = [
                    {
                        "doc_id": doc_id,
                        "url": doc.get("url", ""),
                        "title": doc.get("title", ""),
                        "chunk_index": batch_start + i
                    }
                    for i in range(len(batch))
                ]

                index.add(embeddings)

                for i in range(len(batch)):
                    metadata.append({
                        "id": batch_ids[i],
                        "doc_id": doc_id,
                        "document": batch[i],
                        "metadata": metadatas[i]
                    })

                logger.info(f"Added {len(batch)} vectors to index (doc {doc_index})")

            except Exception as e:
                logger.error(f"Failed embedding batch for doc {doc_id}: {e}")
                continue

    try:
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(FAISS_METADATA_PATH, "w") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Faiss index and metadata saved successfully")
    except Exception as e:
        logger.error(f"Failed to save Faiss index or metadata: {e}")
        raise

    logger.info(f"Done embedding. Total vectors in index: {index.ntotal}")


