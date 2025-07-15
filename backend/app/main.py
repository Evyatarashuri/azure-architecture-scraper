from fastapi import FastAPI
from celery import chain
from app.tasks.scrape_tasks import fetch_links_task, scrape_each_page_task, embed_all_pages_direct
from app.api import query_endpoint
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/scrape-all")
def scrape_all():
    job_chain = chain(
        fetch_links_task.s().set(queue='links'),
        scrape_each_page_task.s().set(queue='pages'),
        embed_all_pages_direct.s().set(queue='embedding')
    )
    job_chain.apply_async()
    return {"status": "scraping started"}

app.include_router(query_endpoint.router, prefix="/query", tags=["Query"])

