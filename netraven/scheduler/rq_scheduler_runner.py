import logging
from rq_scheduler import Scheduler
from redis import Redis
from netraven.utils.unified_logger import get_unified_logger

class UnifiedLoggerHandler(logging.Handler):
    def emit(self, record):
        logger = get_unified_logger()
        msg = record.getMessage()
        level = record.levelname
        logger.log(
            msg,
            level="DEBUG",
            destinations=["stdout", "file", "db"],
            source=record.name  # e.g., 'rq_scheduler.scheduler'
        )

# set logging level for UnifiedLoggerHandler
unified_handler = UnifiedLoggerHandler()
unified_handler.setLevel(logging.DEBUG)  # Or DEBUG if you want more detail

# rq scheduler logging 
logging.getLogger('rq_scheduler').addHandler(unified_handler)
logging.getLogger('rq_scheduler').setLevel(logging.DEBUG)

# Connect to Redis
redis_url = "redis://redis:6379/0"  # Or use your config/env
conn = Redis.from_url(redis_url)

# Start the scheduler
scheduler = Scheduler(connection=conn)
scheduler.run()  