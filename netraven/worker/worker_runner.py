import logging
from redis import Redis
from rq import Worker
from netraven.utils.unified_logger import get_unified_logger

## Entry point file for starting worker process.

logger = get_unified_logger()

# --- Attach your unified logger handler ---
class UnifiedLoggerHandler(logging.Handler):
    def emit(self, record):
        logger = get_unified_logger()
        msg = record.getMessage()
        level = record.levelname
        logger.log(
            msg,
            level=level,
            destinations=["stdout", "file", "db"],
            source=record.name
        )

unified_handler = UnifiedLoggerHandler()
unified_handler.setLevel(logging.DEBUG)
logging.getLogger('rq.worker').addHandler(unified_handler)
logging.getLogger('rq').addHandler(unified_handler)
logging.getLogger('rq').setLevel(logging.DEBUG)
logging.getLogger('rq.worker').setLevel(logging.DEBUG)
logging.getLogger('rq').propagate = False
logging.getLogger('rq.worker').propagate = False

# --- Start the RQ worker ---
redis_conn = Redis.from_url("redis://redis:6379/0")
logger.log(f"[INFO] Starting rq worker process...", level="INFO", destinations=["stdout", "file", "db"], source="worker")
    
redis_conn = Redis.from_url("redis://redis:6379/0")
worker = Worker(['default', 'high', 'low'], connection=redis_conn)
worker.work()