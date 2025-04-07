import time
import structlog
from redis import Redis
from rq_scheduler import Scheduler

# Assuming config loader exists and works as expected
# from netraven.config.loader import load_config
from netraven.scheduler.job_registration import sync_jobs_from_db

log = structlog.get_logger()

# Placeholder for config loading - replace with actual implementation
def get_scheduler_config():
    # config = load_config(env="dev") # Or determine env dynamically
    # return config.get("scheduler", {})
    # Default values based on scheduler_sot.md for now
    return {
        "redis_url": "redis://localhost:6379/0",
        "polling_interval_seconds": 10,
    }

if __name__ == "__main__":
    config = get_scheduler_config()
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
        # Exit or handle appropriately if Redis connection fails
        exit(1)

    while True:
        log.info("Scheduler polling for jobs...")
        try:
            # In a real implementation, pass the actual scheduler instance
            sync_jobs_from_db(scheduler) 
            log.debug("Job sync process completed.")
        except Exception as e:
            # Catch broad exceptions during the sync process
            log.error("Error during job synchronization", error=str(e), exc_info=True)
        
        log.debug(f"Scheduler sleeping for {polling_interval} seconds.")
        time.sleep(polling_interval)
