from celery import Celery
import os
from dotenv import load_dotenv
import httpx
import uuid
import numpy as np
import json
import faiss
import uuid
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
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL_EMBEDDING = os.getenv("OLLAMA_MODEL_EMBEDDING", "nomic-embed-text")


FAISS_INDEX_PATH = "/app/faiss_store/index.faiss"
FAISS_METADATA_PATH = "/app/faiss_store/metadata.json"


# fetch links task
@celery_app.task(name="fetch_links_task")
def fetch_links_task():
    links_collection = get_links_collection()

    print(f"📊 Found {links_collection.count_documents({})} links in MongoDB")
    print("🔗 Fetching all architecture links...")

    existing_count = links_collection.count_documents({})
    if existing_count >= 352:
        print(f"🛑 Found {existing_count} links in MongoDB — skipping scraping.")
        return

    print("🌐 Scraping links with Selenium...")
    all_links = []
    skip = 0

    while True:
        links = scrape_links(skip)
        if not links:
            break
        insert_architecture_links(links)
        all_links.extend(links)
        skip += 6

    print(f"✅ Total {len(set(all_links))} unique links inserted to MongoDB")


# scrape each page task
@celery_app.task(name="scrape_each_page_task")
def scrape_each_page_task(_=None):
    links_collection = get_links_collection()
    pages_collection = get_pages_collection()

    print("📄 Loading links from MongoDB and scraping each page...")

    existing_count = pages_collection.count_documents({})
    print(f"📊 Found {existing_count} pages in MongoDB")

    if existing_count >= 352:
        print(f"🛑 Found {existing_count} pages in MongoDB — skipping scraping.")
        return

    urls = [doc["url"] for doc in links_collection.find({})]
    total = len(urls)
    print(f"🔢 Total URLs to scrape: {total}")

    for i, url in enumerate(urls, start=1):
        try:
            if insert_architecture_page_data({"url": url}, check_only=True):
                print(f"⏭️ [{i}/{total}] Skipping {url} - already in MongoDB.")
                continue

            data = scrape_architecture_page(url)
            insert_architecture_page_data(data)

            print(f"✅ [{i}/{total}] Saved to MongoDB: {url}")

        except Exception as e:
            print(f"❌ [{i}/{total}] Failed for {url}: {e}")


# Function to get embeddings from Ollama
def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    print(f"📤 Sending texts to Ollama for embedding: ...")
    
    response = httpx.post(
        f"{OLLAMA_URL}/api/embed",
        json={"model": OLLAMA_MODEL_EMBEDDING, "input": texts},
        timeout=120.0
    )

    print(f"📬 Received response from Ollama: {response.status_code}")

    response.raise_for_status()

    data = response.json()
    if "embeddings" in data:
        print(f"✅ Successfully received embeddings with {len(data['embeddings'])} entries.")
    else:
        print("❌ No embeddings found in the response.")

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


# embed all pages task
@celery_app.task(name="embed_all_pages_direct")
def embed_all_pages_direct(_=None):
    faiss_store_dir = os.path.dirname(FAISS_INDEX_PATH)
    try:
        os.makedirs(faiss_store_dir, exist_ok=True)
        print(f"📂 Ensured faiss_store exists: {faiss_store_dir}")
        print(f"📂 faiss_store contents: {os.listdir(faiss_store_dir)}")
    except Exception as e:
        print(f"❌ Failed to create/check faiss_store: {str(e)}")
        raise

    
    dimension = 768
    index = faiss.IndexFlatL2(dimension)
    metadata = []
    processed_doc_ids = set()

    if os.path.exists(FAISS_INDEX_PATH):
        try:
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(FAISS_METADATA_PATH, "r") as f:
                metadata = json.load(f)

            processed_doc_ids = {entry["id"].split("-")[0] for entry in metadata}
            print(f"✅ Loaded existing Faiss index with {index.ntotal} vectors")
            print(f"📂 faiss_store contents after loading: {os.listdir(faiss_store_dir)}")
            print(f"📋 Processed document IDs: {len(processed_doc_ids)}")
        except Exception as e:
            print(f"❌ Failed to load Faiss index or metadata: {str(e)}")
            raise

    pages_collection = get_pages_collection()
    print("📚 Loading documents from MongoDB...")
    documents = list(pages_collection.find({"_id": {"$nin": list(processed_doc_ids)}}))
    total_docs = len(documents)
    embedded_chunks = 0

    print(f"🔢 Total documents to process: {total_docs}")

    for doc_index, doc in enumerate(documents, start=1):
        uid = str(doc["_id"])
        print(f"\n🔍 Embedding doc {doc_index}/{total_docs} | ID: {uid}")

        content = f"{doc.get('title', '')}\n{' '.join(doc.get('tags', []))}\n{doc.get('content', '')}"
        chunks = chunk_text(content)

        if not chunks:
            print(f"⚠️ Skipping empty doc {uid}")
            continue

        batch_size = 10
        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            batch_ids = [f"{uid}-{str(uuid.uuid4())}" for _ in range(len(batch))]

            try:
                print(f"📤 Sending batch {batch_start + 1}–{batch_start + len(batch)} to Ollama...")
                embeddings = get_embeddings_batch(batch)
                embeddings = np.array(embeddings, dtype=np.float32)
                print(f"✅ Received {len(embeddings)} embeddings.")

                if len(batch_ids) != len(batch) or len(batch) != len(embeddings):
                    raise ValueError(
                        f"Batch size mismatch: {len(batch_ids)} IDs, {len(batch)} documents, {len(embeddings)} embeddings"
                    )

                if embeddings.shape[1] != dimension:
                    raise ValueError(f"Embedding dimension mismatch: expected {dimension}, got {embeddings.shape[1]}")
                for i, emb in enumerate(embeddings):
                    if np.any(np.isnan(emb)) or np.any(np.isinf(emb)):
                        raise ValueError(f"NaN or inf found in embedding at index {i}: {emb}")

                metadatas = [
                    {
                        "url": doc.get("url", ""),
                        "title": doc.get("title", ""),
                        "chunk_index": batch_start + i
                    }
                    for i in range(len(batch))
                ]
                if len(metadatas) != len(batch):
                    raise ValueError(f"Metadata mismatch: {len(metadatas)} metadatas, {len(batch)} documents")

                print(f"💾 Adding to Faiss: {len(batch)} items")
                print(f"📋 Sample ID: {batch_ids[0]}")
                print(f"📋 Sample document: {batch[0][:100]}...")
                print(f"📋 Sample embedding: {embeddings[0][:5]}... (length: {embeddings.shape[1]})")
                print(f"📋 Sample metadata: {metadatas[0]}")

                index.add(embeddings)

                for i in range(len(batch)):
                    metadata.append({
                        "id": batch_ids[i],
                        "document": batch[i],
                        "metadata": metadatas[i]
                    })

                embedded_chunks += len(batch)
                print(f"✅ Inserted {len(batch)} items into Faiss.")
                print(f"📦 Current vectors in Faiss: {index.ntotal}")

                if embedded_chunks % 10 == 0:
                    try:
                        faiss.write_index(index, FAISS_INDEX_PATH)
                        with open(FAISS_METADATA_PATH, "w") as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                        print(f"✅ Saved Faiss index and metadata after {embedded_chunks} items")
                        print(f"📂 faiss_store contents after saving: {os.listdir(faiss_store_dir)}")
                    except Exception as e:
                        print(f"❌ Failed to save Faiss index or metadata: {str(e)}")
                        raise

            except Exception as e:
                print(f"❌ Failed embedding batch {batch_start + 1} for doc {uid}: {str(e)}")
                print(f"Batch IDs sample: {batch_ids[:2]}...")
                print(f"Batch documents sample: {batch[:2]}...")
                print(f"Batch embeddings sample: {embeddings[:2]}...")
                continue

        processed_doc_ids.add(uid)

    try:
        faiss.write_index(index, FAISS_INDEX_PATH)
        with open(FAISS_METADATA_PATH, "w") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"✅ Final save of Faiss index and metadata to {FAISS_INDEX_PATH} and {FAISS_METADATA_PATH}")
        print(f"📂 faiss_store contents after final save: {os.listdir(faiss_store_dir)}")
    except Exception as e:
        print(f"❌ Failed to save final Faiss index or metadata: {str(e)}")
        raise

    print(f"🎉 Done. Total vectors added to Faiss: {embedded_chunks}")
    print(f"📦 Final total vectors in Faiss: {index.ntotal}")
    print(f"📋 Sample metadata from Faiss: {metadata[:2] if metadata else []}")


