from datetime import datetime, timezone
import structlog
from rq_scheduler import Scheduler
from sqlalchemy.orm import Session
from netraven.utils.unified_logger import get_unified_logger

# Database imports - adjust paths if necessary
from netraven.db.session import get_db
from netraven.db.models import Job # Assuming Job model exists as defined

# Job definition import
from netraven.scheduler.job_definitions import run_device_job
from netraven.worker.runner import run_job as run_worker_job # Use correct worker function import

def generate_rq_job_id(db_job_id: int) -> str:
    return f"netraven_db_job_{db_job_id}"

def sync_jobs_from_db(scheduler: Scheduler):
    """Fetches enabled jobs from the database and schedules them using RQ Scheduler.
    
    Ensures jobs are scheduled according to their type (interval, cron, onetime)
    and avoids duplicate scheduling.
    Args:
        scheduler: The RQ Scheduler instance.
    """
    logger = get_unified_logger()
    logger.log(
        "Starting job synchronization from database...",
        level="DEBUG",
        destinations=["stdout"],
        source="scheduler_job_registration",
    )
    db: Session | None = None
    try:
        db = next(get_db())
        jobs_to_schedule = db.query(Job).filter(Job.is_enabled == True).all()
        logger.log(
            f"Found {len(jobs_to_schedule)} enabled jobs in DB.",
            level="INFO",
            destinations=["stdout"],
            source="scheduler_job_registration",
        )

        # Get existing scheduled jobs from RQ Scheduler to compare
        # Note: scheduler.get_jobs() returns RQ Job instances
        scheduled_rq_jobs = scheduler.get_jobs()
        # Create a set of the predictable RQ job IDs that are currently scheduled
        existing_rq_job_ids = {job.id for job in scheduled_rq_jobs}
        logger.log(
            f"{len(existing_rq_job_ids)} jobs currently in RQ-Scheduler.",
            level="DEBUG",
            destinations=["stdout"],
            source="scheduler_job_registration",
        )

        scheduled_count = 0
        skipped_count = 0
        error_count = 0

        for db_job in jobs_to_schedule:
            rq_job_id = generate_rq_job_id(db_job.id)
            job_log_details = {"db_job_id": db_job.id, "job_name": db_job.name, "rq_job_id": rq_job_id}

            # --- Check if job already exists in scheduler --- 
            if rq_job_id in existing_rq_job_ids:
                # TODO: Optional - Check if schedule parameters (interval, cron) changed?
                # If params changed, we might need to cancel the old one and reschedule.
                # For now, just skip if the ID exists.
                logger.log(
                    f"Job already scheduled in RQ-Scheduler, skipping. {job_log_details}",
                    level="DEBUG",
                    destinations=["stdout"],
                    source="scheduler_job_registration",
                )
                skipped_count += 1
                continue

            # --- Schedule based on type --- 
            try:
                if not db_job.is_enabled:
                    logger.log(
                        f"Job is disabled, skipping. {job_log_details}",
                        level="DEBUG",
                        destinations=["stdout"],
                        source="scheduler_job_registration",
                    )
                    skipped_count += 1
                    continue
                
                if db_job.schedule_type == 'interval' and db_job.interval_seconds and db_job.interval_seconds > 0:
                    scheduler.schedule(
                        scheduled_time=datetime.now(timezone.utc), # Start ASAP, interval defines repeats
                        func=run_worker_job,
                        args=[db_job.id],
                        interval=db_job.interval_seconds,
                        repeat=None, # None means repeat indefinitely
                        job_id=rq_job_id, 
                        description=f"NetRaven Job {db_job.id} ({db_job.name}) - Interval",
                        meta={'db_job_id': db_job.id, 'schedule_type': 'interval'}
                    )
                    logger.log(
                        f"Scheduled interval job '{db_job.name}' (interval: {db_job.interval_seconds}s)",
                        level="INFO",
                        destinations=["stdout", "db"],
                        job_id=db_job.id,
                        source="scheduler_job_registration",
                    )
                    scheduled_count += 1
                
                elif db_job.schedule_type == 'cron' and db_job.cron_string:
                    scheduler.cron(
                        db_job.cron_string,
                        func=run_worker_job,
                        args=[db_job.id],
                        repeat=None,
                        job_id=rq_job_id,
                        description=f"NetRaven Job {db_job.id} ({db_job.name}) - Cron",
                        meta={'db_job_id': db_job.id, 'schedule_type': 'cron'}
                    )
                    logger.log(
                        f"Scheduled cron job '{db_job.name}' (cron: {db_job.cron_string})",
                        level="INFO",
                        destinations=["stdout", "db"],
                        job_id=db_job.id,
                        source="scheduler_job_registration",
                    )
                    scheduled_count += 1

                elif db_job.schedule_type == 'onetime' and db_job.scheduled_for:
                    run_time = db_job.scheduled_for
                    # Ensure the scheduled time is in the future
                    if run_time > datetime.now(run_time.tzinfo): # Compare using same timezone awareness
                        scheduler.enqueue_at(
                            run_time,
                            run_worker_job,
                            args=[db_job.id],
                            job_id=rq_job_id,
                            description=f"NetRaven Job {db_job.id} ({db_job.name}) - Onetime",
                            meta={'db_job_id': db_job.id, 'schedule_type': 'onetime'}
                        )
                        logger.log(
                            f"Scheduled one-time job '{db_job.name}' for {run_time}",
                            level="INFO",
                            destinations=["stdout", "db"],
                            job_id=db_job.id,
                            source="scheduler_job_registration",
                        )
                        scheduled_count += 1
                    else:
                        logger.log(
                            f"One-time job '{db_job.name}' scheduled in the past for {run_time}, skipping",
                            level="WARNING",
                            destinations=["stdout", "db"],
                            job_id=db_job.id,
                            source="scheduler_job_registration",
                        )
                        skipped_count += 1
                else:
                    # Skip if no valid schedule type or parameters are set
                    logger.log(
                        f"Job '{db_job.name}' has no valid schedule type/params, skipping",
                        level="WARNING",
                        destinations=["stdout", "db"],
                        job_id=db_job.id,
                        source="scheduler_job_registration",
                    )
                    skipped_count += 1
            
            except Exception as schedule_e:
                logger.log(
                    f"Failed to schedule job '{db_job.name}': {schedule_e}",
                    level="ERROR",
                    destinations=["stdout", "db"],
                    job_id=db_job.id,
                    source="scheduler_job_registration",
                )
                error_count += 1

        logger.log(
            f"Finished job synchronization. Total enabled: {len(jobs_to_schedule)}, newly scheduled: {scheduled_count}, skipped: {skipped_count}, errors: {error_count}",
            level="INFO",
            destinations=["stdout", "db"],
            source="scheduler_job_registration",
        )

    except Exception as e:
        logger.log(
            f"Error during database query or setup: {e}",
            level="ERROR",
            destinations=["stdout"],
            source="scheduler_job_registration",
        )
    finally:
        if db:
            db.close()
            logger.log(
                "Database session closed.",
                level="DEBUG",
                destinations=["stdout"],
                source="scheduler_job_registration",
            )
