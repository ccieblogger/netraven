# NetRaven UI — Low‑Fidelity Wireframes

*(ASCII block sketches for every primary and secondary view; hi‑fi mock‑ups will replace or accompany these as they are produced.)*

## Legend

```
┌───────┐  Container / Card Border
│ txt   │  Text / Control / Data Cell
└───────┘
● status indicator   ✅ pass  ❌ fail  ⏳ running
```

---

## 1. Main Dashboard (`/`)

```
┌───────────────────────────────────────────────┐
│ KPI  KPI  KPI  KPI                            │
├───────────────────────────────────────────────┤
│ ● API  ● Redis  ● Workers  ● DB              │
├───────────────────────────────────────────────┤
│ Recent Jobs (10)                              │
│ ┌──┬────┬───────┬───────┬────────┐            │
│ │ID│Type│Status │Dur.  │Started │            │
│ └──┴────┴───────┴───────┴────────┘            │
├───────────────────────────────────────────────┤
│ Log Peek ▸                                    │
└───────────────────────────────────────────────┘
```

---

## 2. Job List (`/jobs`)

```
┌───────────────────────────────────────────────┐
│ Filters: [Type▾] [Status▾] [Date▾]  🔍search  │
├───────────────────────────────────────────────┤
│ ID   Type        Devices  Status  Duration…   │
│ f9c8 device_backup   42    ✅      0:12s       │
│ 71ae reachability     1    ❌      0:03s       │
└───────────────────────────────────────────────┘
```

---

## 3. Job Detail (`/jobs/:id`)

```
┌───────────────┬─────────────────────────────────┐
│ Metadata      │ Live Log Stream                 │
│ • Type        │ [▣ auto‑scroll] [⏸ pause]       │
│ • Devices     │ 16:40:01 backup ok edge‑sw‑01   │
│ • Started     │ 16:40:02 backup ok edge‑sw‑02   │
│ • Duration    │ …                               │
└───────────────┴─────────────────────────────────┘
Result Artifacts ▾ (download diff)
```

---

## 4. System Status (`/status`)

```
┌──── API ● │ Redis ● │ RQ ● │ DB ● ─────┐
│ Worker‑A idle 3h │ Worker‑B run 2 │ … │
└─────────────────────────────────────────┘
```

---

## 5. Device List (`/devices`)

```
┌────────────────────────────────────────────────────────────────┐
│ [Add Device]  Filter: [Tag▾] [Reachability▾]  🔍search        │
├────────────────────────────────────────────────────────────────┤
│ Hostname      Serial        Type      Mgmt‑IP   Tags   Status │
│ edge‑sw‑01    JAE0938D2G8   IOS‑XE    10.0.0.2  core   ✅     │
│ access‑ap‑17  9A2C0183GHK   AP        10.0.5.17 wifi  ❌     │
└────────────────────────────────────────────────────────────────┘
```

---

## 6. Device Detail (`/devices/:id`)

```
┌────────────────────────────────────────────────────────────┐
│ Hostname edge‑sw‑01          [Edit] [Delete]              │
├────────────────────────────────────────────────────────────┤
│ Serial: JAE0938D2G8   Model: C9300‑24E   OS: 17.9.3       │
│ Mgmt‑IP: 10.0.0.2     Tags: core, access                  │
├────────────────────────────────────────────────────────────┤
│ Tabs: Overview · Jobs · Backups · Logs                    │
│ (Overview)                                                │
│ • Latest backup: 2025‑04‑26 16:40Z  ✅                    │
│ • Last reachability: 0:03 ago  ✅                         │
└────────────────────────────────────────────────────────────┘
```

---

## 7. Add / Edit Device (Modal)

```
┌ Add Device ───────────────────────────────────────────────┐
│ Hostname  [___________]                                   │
│ Serial    [___________]                                   │
│ Mgmt‑IP   [___ . ___ . ___ . ___ ]                        │
│ Tags      [ core ▾ ]   +[ add ]                           │
│ Credential [ SSH‑Default ▾ ]                              │
│ [Cancel]                 [Save]                           │
└───────────────────────────────────────────────────────────┘
```

---

## 8. Tag List (`/tags`)

```
┌ [Add Tag] ───────────────────────────────────────────────┐
│ Name   Colour   #Devices  Actions                        │
│ core   green     42       ✎  🗑                           │
│ wifi   purple    58       ✎  🗑                           │
└──────────────────────────────────────────────────────────┘
```

---

## 9. Credential List (`/credentials`)

```
┌ [Add Cred] Filters: [Method▾] [Success▾]  🔍search ┐
├────────────────────────────────────────────────────┤
│ Name     Method User success‑rate  Last used      │
│ SSH‑Def  SSH    netops   98 %       2025‑04‑26     │
│ SNMP‑RO  SNMP   readonly 85 %       2025‑04‑25     │
└────────────────────────────────────────────────────┘
```

---

## 10. User List (`/users`)

```
┌ [Add User] ───────────────────────────────────────────────┐
│ Username   Role     Last Login        Status  Actions     │
│ bsmith     admin    2025‑04‑26 11:02  active  ✎  🔒       │
│ noc‑op     viewer   2025‑04‑26 07:19  active  ✎  🔒       │
└───────────────────────────────────────────────────────────┘
```

---

## 11. Backup List (`/backups`)

```
┌ Filters: [Device▾] [Date▾]  🔍search ─────────────────────┐
├───────────────────────────────────────────────────────────┤
│ Device       Taken‑at             Size   Diff vs prev 🔍 │
│ edge‑sw‑01   2025‑04‑26 16:40Z    28 KB  ▶︎              │
│ edge‑sw‑02   2025‑04‑26 16:41Z    27 KB  ▶︎              │
└───────────────────────────────────────────────────────────┘
```

---

## 12. Config Diff (`/backups/:deviceId/:backupId/diff`)

```
┌ edge‑sw‑01  2025‑04‑26 16:40 vs 2025‑04‑25 16:40 ───────┐
│ left‑pane (old)              | right‑pane (new)         │
│ − vlan 10 name USERS         | − vlan 10 name STAFF     │
│                              | + vlan 30 name CONTRACT  │
└──────────────────────────────────────────────────────────┘
```

---

## 13. Global Log Stream (`/logs`)

```
┌ All | Job | Device | System  ⏸ ▣ auto‑scroll 🔍filter ┐
│ 2025‑04‑26 16:40:01  INFO Job 71ae started…            │
│ 2025‑04‑26 16:40:03  ERROR edge‑sw‑99 ssh auth fail    │
└─────────────────────────────────────────────────────────┘
```

---

## 14. Scheduled Jobs & Queue Status (`/scheduler`)

```
┌──────────────────────────────────────────────────────────────┐
│ Scheduled Jobs                                              │
├────┬─────────────┬─────────────┬─────────────┬─────────────┤
│ ID │ Name        │ Type        │ Schedule    │ Next Run    │
├────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ 12 │ Backup Core │ backup      │ every 1h    │ 13:00       │
│ 13 │ Reach Wifi  │ reachability│ every 5 min │ 12:45       │
└────┴─────────────┴─────────────┴─────────────┴─────────────┘

Queue Status
┌───────────────────────────────┐
│ Jobs in Queue: 2             │
├────┬─────────────┬───────────┤
│ ID │ Type        │ Enqueued  │
├────┼─────────────┼───────────┤
│ 14 │ backup      │ 12:44     │
│ 15 │ reachability│ 12:44     │
└────┴─────────────┴───────────┘

[Refresh] [Force Re-Schedule] [Remove Job] (future controls)
└──────────────────────────────────────────────────────────────┘
```

---

## 15. Job Monitor (Modern Refactor)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Job Monitor: [Job Name] (#ID)   [Status Badge]   [Started: 12:45] [Duration]│
│ ─────────────────────────────────────────────────────────────────────────── │
│ Devices: 12   |   Type: Backup   |   Triggered by: admin   |   [Retry] [Cancel]
│ ─────────────────────────────────────────────────────────────────────────── │
│ Live Log Stream [⏸ Pause] [▣ Auto-scroll] [🔍 Filter] [⚙️ Settings]         │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ [16:40:01] INFO backup ok edge‑sw‑01                                   │ │
│ │ [16:40:02] ERROR ssh auth fail edge‑sw‑99                              │ │
│ │ ...                                                                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│ Device Results [Table: Device | Status | Start | End | Actions (View Log)]  │
│ ┌─────────────┬─────────┬────────────┬────────────┬───────────────┐         │
│ │ edge‑sw‑01  │ ✅      │ 12:45:01   │ 12:45:10   │ [View Log]    │         │
│ │ edge‑sw‑99  │ ❌      │ 12:45:02   │ 12:45:05   │ [View Log]    │         │
│ └─────────────┴─────────┴────────────┴────────────┴───────────────┘         │
│ Artifacts: [Download Config] [View Diff]                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

- Header: Job name, ID, status badge, start time, duration, and quick actions.
- Metadata Row: Devices, type, triggered by, and main controls.
- Live Log Stream: Large, scrollable, with controls for pause, auto-scroll, filter, and settings.
- Device Results Table: Compact, sortable, with status icons and quick log access.
- Artifacts: Download and diff buttons for job outputs.
- Color Palette: Use NetRaven's dark theme, status colors (green, red, yellow), and modern iconography.
- Responsiveness: Collapsible sections or stacked layout on mobile.

---

*End of wireframes*

