import logging


FORMAT = "%(asctime)s [%(levelname)s] [%(task_name)s:%(task_id)s] %(message)s"

class CeleryContextFilter(logging.Filter):
    """Custom filter to add Celery task context to log records."""
    def filter(self, record):
        record.task_name = getattr(record, 'task_name', 'no-task')
        record.task_id = getattr(record, 'task_id', 'no-id')
        return True


logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
)

logger = logging.getLogger("embedding_logger")
logger.addFilter(CeleryContextFilter())