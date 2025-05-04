# NetRaven Dashboard KPI Health Logic

**Feature Branch:** issue/99-Dashboard-wiring
**Phase:** 1 (Documentation)
**Date:** [Fill in date on commit]

---

## KPI Cards & Health Logic

| KPI Card    | Field in `/jobs/status` | Healthy Logic                                                                 | Values                |
|-------------|------------------------|-------------------------------------------------------------------------------|-----------------------|
| API         | `api`                  | Endpoint responds (API process running)                                       | "healthy"            |
| PostgreSQL  | `postgres`             | Simple DB query (e.g., `SELECT 1`) succeeds                                   | "healthy"/"unhealthy"|
| Redis       | `redis_uptime`         | Uptime present and >0                                                         | >0 = healthy          |
| Worker      | `workers`              | At least one RQ worker present in array                                       | array not empty       |
| Scheduler   | `scheduler`            | Scheduler process detected (heartbeat, PID, or Redis key)                     | "healthy"/"unhealthy"|
| RQ          | `rq_queues`            | Array present with queue/job stats                                            | array not empty       |

---

## Field Details & Logic

### 1. API (FastAPI)
- **Field:** `api`
- **Healthy:** If `/jobs/status` responds, set to `"healthy"`.
- **Unhealthy:** Only if endpoint fails (implicit).
- **Notes:** Optionally include version info.

### 2. PostgreSQL
- **Field:** `postgres`
- **Healthy:** Simple DB query (e.g., `SELECT 1`) succeeds.
- **Unhealthy:** Query fails (DB unreachable or error).

### 3. Redis
- **Field:** `redis_uptime`
- **Healthy:** Field present and >0.
- **Unhealthy:** Field missing or 0.

### 4. Worker
- **Field:** `workers`
- **Healthy:** Array present and not empty (at least one worker running).
- **Unhealthy:** Array empty or missing.

### 5. Scheduler
- **Field:** `scheduler`
- **Healthy:** Scheduler process detected (heartbeat, PID, or Redis key).
- **Unhealthy:** Not detected.

### 6. RQ
- **Field:** `rq_queues`
- **Healthy:** Array present (queue/job stats available).
- **Unhealthy:** Array missing or empty.

---

## Implementation Notes
- All fields should be present in `/jobs/status` for frontend consumption.
- If a check cannot be performed, set value to `"unknown"`.
- This logic will be referenced in backend implementation and API docs.

---

**End of Phase 1** 