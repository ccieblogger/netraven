import time
from redis import Redis
from rq_scheduler import Scheduler

# Use the central config loader
from netraven.config.loader import load_config
from netraven.scheduler.job_registration import sync_jobs_from_db
from netraven.utils.unified_logger import get_unified_logger

# No longer need the placeholder function
# def get_scheduler_config(): ...

if __name__ == "__main__":
    # Load configuration using the central loader
    full_config = load_config()
    config = full_config.get("scheduler", {}) # Get the scheduler specific section

    # Get settings from config, providing defaults
    redis_url = config.get("redis_url", "redis://localhost:6379/0")
    polling_interval = config.get("polling_interval_seconds", 10)

    logger = get_unified_logger()
    logger.log(
        f"Starting NetRaven Scheduler",
        level="INFO",
        destinations=["stdout"],
        source="scheduler_runner",
        extra={"redis_url": redis_url, "poll_interval": polling_interval},
    )

    try:
        redis_conn = Redis.from_url(redis_url)
        redis_conn.ping() # Test connection
        logger.log(
            "Successfully connected to Redis.",
            level="INFO",
            destinations=["stdout"],
            source="scheduler_runner",
        )
        scheduler = Scheduler(connection=redis_conn)
    except Exception as e:
        logger.log(
            f"Failed to connect to Redis or initialize scheduler: {e}",
            level="ERROR",
            destinations=["stdout"],
            source="scheduler_runner",
            extra={"redis_url": redis_url},
        )
        exit(1)

    while True:
        logger.log(
            "Scheduler polling for jobs...",
            level="INFO",
            destinations=["stdout"],
            source="scheduler_runner",
        )
        try:
            # Pass the scheduler instance to the sync function
            sync_jobs_from_db(scheduler)
            logger.log(
                "Job sync process completed.",
                level="DEBUG",
                destinations=["stdout"],
                source="scheduler_runner",
            )
        except Exception as e:
            logger.log(
                f"Error during job synchronization: {e}",
                level="ERROR",
                destinations=["stdout"],
                source="scheduler_runner",
            )

        logger.log(
            f"Scheduler sleeping for {polling_interval} seconds.",
            level="DEBUG",
            destinations=["stdout"],
            source="scheduler_runner",
        )
        time.sleep(polling_interval)
