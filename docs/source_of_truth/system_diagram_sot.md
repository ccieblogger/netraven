# NetRaven System Architecture Diagram (ASCII)

This diagram illustrates the interaction between NetRaven’s core components.

```
                        ┌────────────────────┐
                        │     Frontend UI    │
                        │   (Vue / REST)   │
                        └────────▲───────────┘
                                 │ REST API
                                 │
                        ┌────────┴───────────┐
                        │     API Service    │
                        │     (FastAPI)      │
                        └───────▲────────────┘
                                │
             ┌──────────────────┼────────────────────┐
             │                  │                    │
      Device │          Job CRUD│           User/Auth│
     Records │                  ▼                    ▼
         ┌───┴─────┐     ┌──────────────┐      ┌──────────────┐
         │ Devices │     │  Jobs Table  │      │  Users/Roles │
         └───┬─────┘     └──────┬───────┘      └────┬─────────┘
             │                  │                   │
             │                  ▼                   │
             │        ┌───────────────┐             │
             │        │   Scheduler   │◄─────┐      │
             │        │   (RQ Only)│      │      │
             │        └──────┬────────┘      │      │
             │               │               │      │
             ▼               ▼               ▼      ▼
      ┌────────────┐  ┌──────────────┐  ┌──────────────┐
      │ PostgreSQL │  │ RQ + RQ Scheduler │  │ JWT Security │
      └────┬───────┘  └──────┬───────┘  └──────────────┘
           │                 │
           ▼                 ▼
   ┌─────────────────────────────────┐
   │     Device Communication        │
   │        (device_comm)          ─ │
   └────────────┬────────────────────┘
                │                 ▲
                ▼                 │
       ┌───────────────────┐      │
       │  Netmiko (SSH/API)│      │ 
       └────────┬──────────┘      │
                │                 │
                ▼                 │
        ┌─────────────┐           │
        │ Network Gear│           │
        └─────────────┘           │
                                  ▼
        ┌──────────────────────────────────┐
        │ Git Repo (configs & versioning)  │
        └──────────────────────────────────┘
```

