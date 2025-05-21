from netraven.utils.unified_logger import get_unified_logger
from netraven.worker.jobs.base import ParamsModel
import subprocess
import socket

class Params(ParamsModel):
    """
    Example Params for reachability job. Extend as needed for real parameters.
    """
    # Example: timeout: int = 2
    pass

JOB_META = {
    "label": "Reachability Check",
    "description": "Performs ICMP and TCP reachability checks on the device.",
    "icon": "mdi-lan-connect",
    "default_schedule": "hourly"
}

logger = get_unified_logger()

def run(device, job_id, config, db):
    device_id = getattr(device, 'id', None)
    device_name = getattr(device, 'hostname', None)
    job_type = "reachability"
    logger.log(
        f"Starting reachability check for job_id={job_id}, device_id={device_id}",
        level="INFO",
        destinations=["stdout", "file", "db"],
        log_type="job",
        source=f"worker.job.{job_type}",
        job_id=job_id,
        device_id=device_id
    )
    device_ip = getattr(device, 'ip_address', None)
    result = {
        "device_id": device_id,
        "device_name": device_name,
        "success": False,
        "details": {
            "icmp_ping": {},
            "tcp_22": {},
            "tcp_443": {},
            "errors": []
        }
    }
    # ICMP Ping
    try:
        logger.log(
            f"Attempting to ping device at {device_ip} hostname={device_name}, device_id={device_id}",
            level="INFO",
            destinations=["stdout", "file", "db"],
            log_type="job",
            source=f"worker.job.{job_type}",
            job_id=job_id,
            device_id=device_id
        )
        ping_cmd = ["ping", "-c", "1", "-W", "2", device_ip]
        ping_proc = subprocess.run(ping_cmd, capture_output=True, text=True)
        if ping_proc.returncode == 0:
            result["details"]["icmp_ping"] = {"success": True, "latency": "OK"}
        else:
            result["details"]["icmp_ping"] = {"success": False, "error": ping_proc.stderr or "Ping failed"}
    except Exception as e:
        result["details"]["icmp_ping"] = {"success": False, "error": str(e)}
        result["details"]["errors"].append(str(e))
    # TCP Port Checks
    for port in [22, 443]:
        try:
            sock = socket.create_connection((device_ip, port), timeout=2)
            sock.close()
            result["details"][f"tcp_{port}"] = {"success": True}
        except Exception as e:
            result["details"][f"tcp_{port}"] = {"success": False, "error": str(e)}
    # Mark job as successful if ANY test succeeded
    result["success"] = (
        result["details"]["icmp_ping"].get("success") or
        result["details"]["tcp_22"].get("success") or
        result["details"]["tcp_443"].get("success")
    )
    # --- Device-level job log for reachability ---
    try:
        if result["success"]:
            logger.log(
                "Reachability check completed successfully.",
                level="INFO",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
        else:
            error_msgs = []
            if not result["details"]["icmp_ping"].get("success"):
                error_msgs.append(f"ICMP: {result['details']['icmp_ping'].get('error','failed')}")
            for port in [22, 443]:
                if not result["details"][f"tcp_{port}"].get("success"):
                    error_msgs.append(f"TCP {port}: {result['details'][f'tcp_{port}'].get('error','failed')}")
            msg = "Reachability check failed: " + "; ".join(error_msgs)
            logger.log(
                msg,
                level="WARNING",
                destinations=["stdout", "file", "db"],
                log_type="job",
                source=f"worker.job.{job_type}",
                job_id=job_id,
                device_id=device_id
            )
    except Exception as log_exc:
        logger.log(
            f"Exception in reachability logging for job_id={job_id}, device_id={device_id}: {log_exc}",
            level="ERROR",
            destinations=["stdout", "file", "db"],
            log_type="job",
            source=f"worker.job.{job_type}",
            job_id=job_id,
            device_id=device_id
        )
    return result
