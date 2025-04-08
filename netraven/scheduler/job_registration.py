from datetime import datetime, timezone
import structlog
from rq_scheduler import Scheduler
from sqlalchemy.orm import Session

# Database imports - adjust paths if necessary
from netraven.db.session import get_db
from netraven.db.models import Job # Assuming Job model exists as defined

# Job definition import
from netraven.scheduler.job_definitions import run_device_job
from netraven.worker.runner import run_job as run_worker_job # Use correct worker function import

log = structlog.get_logger()

# Function to generate a predictable RQ job ID from our DB Job ID
def generate_rq_job_id(db_job_id: int) -> str:
    return f"netraven_db_job_{db_job_id}"

def sync_jobs_from_db(scheduler: Scheduler):
    """Fetches enabled jobs from the database and schedules them using RQ Scheduler.
    
    Ensures jobs are scheduled according to their type (interval, cron, onetime)
    and avoids duplicate scheduling.
    Args:
        scheduler: The RQ Scheduler instance.
    """
    log.debug("Starting job synchronization from database...")
    db: Session | None = None
    try:
        db = next(get_db())
        jobs_to_schedule = db.query(Job).filter(Job.is_enabled == True).all()
        log.info(f"Found {len(jobs_to_schedule)} enabled jobs in DB.")

        # Get existing scheduled jobs from RQ Scheduler to compare
        # Note: scheduler.get_jobs() returns RQ Job instances
        scheduled_rq_jobs = scheduler.get_jobs()
        # Create a set of the predictable RQ job IDs that are currently scheduled
        existing_rq_job_ids = {job.id for job in scheduled_rq_jobs}
        log.debug(f"{len(existing_rq_job_ids)} jobs currently in RQ-Scheduler.")

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
                log.debug("Job already scheduled in RQ-Scheduler, skipping.", **job_log_details)
                skipped_count += 1
                continue

            # --- Schedule based on type --- 
            try:
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
                    log.info("Scheduled interval job.", interval=f"{db_job.interval_seconds}s", **job_log_details)
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
                    log.info("Scheduled cron job.", cron=db_job.cron_string, **job_log_details)
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
                        log.info("Scheduled one-time job.", run_at=run_time, **job_log_details)
                        scheduled_count += 1
                    else:
                        log.warning("One-time job scheduled in the past, skipping.", run_at=run_time, **job_log_details)
                        skipped_count += 1
                else:
                    # Skip if no valid schedule type or parameters are set
                    log.warning("Job has no valid schedule type/params, skipping.", 
                                schedule_type=db_job.schedule_type, 
                                interval=db_job.interval_seconds,
                                cron=db_job.cron_string,
                                run_at=db_job.scheduled_for,
                                **job_log_details)
                    skipped_count += 1
            
            except Exception as schedule_e:
                log.error("Failed to schedule job", error=str(schedule_e), exc_info=True, **job_log_details)
                error_count += 1

        log.info("Finished job synchronization.", 
                 total_enabled=len(jobs_to_schedule), 
                 newly_scheduled=scheduled_count, 
                 already_exist_skipped=skipped_count,
                 errors=error_count)

    except Exception as e:
        log.error("Error during database query or setup", error=str(e), exc_info=True)
    finally:
        if db:
            db.close()
            log.debug("Database session closed.")
