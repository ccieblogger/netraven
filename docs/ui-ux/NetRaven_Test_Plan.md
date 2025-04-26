# NetRaven UI — Test Plan (Phase 1)

## 1. Scope
Validate the refactored UI against functional, regression, performance, and accessibility criteria for the following core areas:
* Dashboard & KPIs
* Jobs (list + detail)
* Devices, Tags, Credentials, Users CRUD
* Log streaming & search
* Backups list & config diff
* System Status

---
## 2. Roles & Environments
| Role | Environment | URL pattern |
|------|-------------|-------------|
| Dev | local Vite dev server | `http://localhost:5173` |
| QA | staging | `https://nr‑stg.example.com` |
| Prod | production | `https://nr.example.com` |

---
## 3. Test Matrix
### 3.1 Smoke (run on every PR – Cypress)
| ID | Route | Happy‑path assertion |
|----|-------|----------------------|
| SM‑001 | `/` | KPI cards render; 200 response |
| SM‑002 | `/jobs` | Table rows ≥ 1; filter chips functional |
| SM‑003 | `/jobs/:id` | SSE stream opens (status 200) |
| SM‑004 | `/devices` | “Add Device” button opens modal |
| SM‑005 | `/status` | All service badges show up/down state |

### 3.2 Regression (nightly)
Key CRUD flows for each entity + auth token refresh scenario.

### 3.3 Performance
| Route | Metric | Budget |
|-------|--------|--------|
| `/` | Time‑to‑interactive | < 3 s (desktop cable) |
| `/jobs/:id` SSE latency | new log line ≤ 1 s late |

### 3.4 Accessibility (axe‑core)
All pages must score ≥ 90 / 100; colour contrast AA.

---
## 4. Test Data
* Seed DB with 50 devices, 1 000 jobs, 50 000 logs via fixture script.
* Use `faker` to randomize Hostnames & timestamps.

---
## 5. Tooling & CI
* **Cypress 13** + `@testing-library/cypress`
* GitHub Actions matrix: Node 20 on Ubuntu.
* `npm run test:smoke` on pull‑request, `npm run test:full` on nightly schedule.

---
## 6. Future Phase (v1.1+)
* Mobile viewport tests (375 px) & visual regression (Percy)
* Pen‑test automation (OWASP ZAP) for auth endpoints.

---
*Document version 2025‑04‑26*

