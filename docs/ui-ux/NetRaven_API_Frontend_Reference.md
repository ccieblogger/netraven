# NetRaven REST API – Front‑End Reference
*(Condensed, UI‑oriented contract only; full backend swagger lives under `/docs/architecture`)*

## Conventions
| Aspect | Value |
|--------|-------|
| Base URL | `/api` |
| Auth | `Authorization: Bearer <JWT>` |
| Pagination | `page`, `size` (default 1, 25) |
| Time format | ISO‑8601 UTC strings |

---
## 1. Jobs
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/jobs` | Filter params: `status`, `type`, `device`, `from`, `to` |
| `GET` | `/jobs/{id}` | Detail inc. `log_channel` |
| `POST` | `/jobs` | Trigger new job (bulk or scheduled) |
| `PATCH` | `/jobs/{id}` | Cancel / retry |

### Example `GET /jobs?page=1&size=25`
```json
{
  "items": [ { "id": "71ae", "type": "reachability", … } ],
  "page": 1,
  "size": 25,
  "total": 638
}
```

---
## 2. Logs
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/logs` | Filters: `job_id`, `device_id`, `log_type`, `level` |
| `GET` | `/logs/{id}` | Single entry |
| `GET` | `/logs/stream?job_id={id}` | **SSE** stream (see spec § 8.2) |
| `GET` | `/logs/stats` | Success/fail counts for dashboard KPIs |

---
## 3. Devices
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/devices` | Filters: `tag`, `reachability` |
| `GET` | `/devices/{id}` | Detail inc. serial, interfaces |
| `POST` | `/devices` | Add device |
| `PUT` | `/devices/{id}` | Full update |
| `PATCH` | `/devices/{id}` | Partial update |
| `DELETE` | `/devices/{id}` | Remove |

---
## 4. Tags
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/tags` | List |
| `POST` | `/tags` | Add |
| `PATCH` | `/tags/{id}` | Update |
| `DELETE` | `/tags/{id}` | Delete (cascade optional) |

---
## 5. Credentials
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/credentials` | Filters: `method`, `min_success` |
| `POST` | `/credentials` | Add (payload includes encrypted secret) |
| `PATCH` | `/credentials/{id}` | Update |
| `DELETE` | `/credentials/{id}` | Delete |

*Success‑rate stats* – each credential response object adds `success_rate` (0‑100 %), derived backend‑side.

---
## 6. Users
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/users` | Admin only |
| `POST` | `/users` | Create |
| `PATCH` | `/users/{id}` | Update role / reset pwd |
| `DELETE` | `/users/{id}` | Disable |

---
## 7. Backups
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/backups` | Filters: `device_id`, `from`, `to` |
| `GET` | `/backups/{id}` | Metadata + download URL |
| `GET` | `/backups/{id}/diff?against={prevId}` | Returns diff blob |

---
## 8. System Status
| Verb | Path | Notes |
|------|------|-------|
| `GET` | `/status` | Returns service heartbeat & worker metrics |

---
*Last updated 2025‑04‑26.*

