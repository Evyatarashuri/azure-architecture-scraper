from app.tasks.scrape_tasks import celery_app

# This file allows celery to load the app with:
# celery -A app.celery_worker worker ...
