import time
import structlog
from redis import Redis
from rq_scheduler import Scheduler

# Use the central config loader
from netraven.config.loader import load_config
from netraven.scheduler.job_registration import sync_jobs_from_db

log = structlog.get_logger()

# Configure structlog for basic console output (can be refined later)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer() # Or JSONRenderer for structured logs
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# No longer need the placeholder function
# def get_scheduler_config(): ...

if __name__ == "__main__":
    # Load configuration using the central loader
    full_config = load_config()
    config = full_config.get("scheduler", {}) # Get the scheduler specific section

    # Get settings from config, providing defaults
    redis_url = config.get("redis_url", "redis://localhost:6379/0")
    polling_interval = config.get("polling_interval_seconds", 10)

    log.info("Starting NetRaven Scheduler", redis_url=redis_url, poll_interval=polling_interval)

    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping() # Test connection
        log.info("Successfully connected to Redis.")
        scheduler = Scheduler(connection=redis_conn)
    except Exception as e:
        log.error("Failed to connect to Redis or initialize scheduler", error=str(e), redis_url=redis_url)
        exit(1)

    while True:
        log.info("Scheduler polling for jobs...")
        try:
            # Pass the scheduler instance to the sync function
            sync_jobs_from_db(scheduler)
            log.debug("Job sync process completed.")
        except Exception as e:
            log.error("Error during job synchronization", error=str(e), exc_info=True)

        log.debug(f"Scheduler sleeping for {polling_interval} seconds.")
        time.sleep(polling_interval)
