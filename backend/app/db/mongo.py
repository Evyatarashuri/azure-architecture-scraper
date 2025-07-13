import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "azure_architecture")

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[DB_NAME]
    return _db

def get_links_collection():
    return get_db()["architecture_links"]

def get_pages_collection():
    return get_db()["architecture_pages"]

def insert_architecture_links(links: list[str]):
    collection = get_links_collection()
    for link in links:
        if not collection.find_one({"url": link}):
            collection.insert_one({"url": link})

def insert_architecture_page_data(data: dict, check_only=False):
    collection = get_pages_collection()
    if check_only:
        return collection.find_one({"url": data}) is not None
    collection.replace_one({"url": data["url"]}, data, upsert=True)
