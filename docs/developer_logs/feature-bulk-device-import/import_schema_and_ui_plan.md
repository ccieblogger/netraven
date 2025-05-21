# Bulk Device Import: Schema & UI Plan

**Date:** 2025-05-20
**Branch:** issue/133-bulk-2way-ws1

## Import Schema (CSV/JSON)

### Required Fields
- `hostname` (string, required, unique)
- `ip_address` (IPv4/IPv6, required, unique)
- `device_type` (string, required, must match allowed types)

### Optional Fields
- `port` (integer, default: 22)
- `description` (string)
- `serial_number` (string)
- `model` (string)
- `source` (string, default: "imported")
- `notes` (string)
- `tags` (list of tag IDs, e.g. [1,2])

### Example CSV
```csv
hostname,ip_address,device_type,port,description,serial_number,model,source,notes,tags
core-sw-01,10.0.0.2,cisco_ios,22,Core switch,FTX1234A1B2,Catalyst 9300,imported,"Main rack",1|2
edge-ap-17,10.0.5.17,arista_eos,22,Edge AP,9A2C0183GHK,Arista 720XP,imported,,2
```
- Use `|` to separate multiple tag IDs in the `tags` column.

### Example JSON
```json
[
  {
    "hostname": "core-sw-01",
    "ip_address": "10.0.0.2",
    "device_type": "cisco_ios",
    "port": 22,
    "description": "Core switch",
    "serial_number": "FTX1234A1B2",
    "model": "Catalyst 9300",
    "source": "imported",
    "notes": "Main rack",
    "tags": [1,2]
  },
  {
    "hostname": "edge-ap-17",
    "ip_address": "10.0.5.17",
    "device_type": "arista_eos",
    "port": 22,
    "serial_number": "9A2C0183GHK",
    "model": "Arista 720XP",
    "source": "imported",
    "tags": [2]
  }
]
```

---

## UI Plan

### Dedicated Bulk Import Page (`/devices/bulk-import`)
- File upload (CSV/JSON)
- Display import schema (table/code block)
- Downloadable sample file (CSV/JSON)
- Results display: success, errors, duplicates
- Explanatory text for schema and process

### Devices Page
- Add "Bulk Import" button (top right, near "Add Device")
- Button links to `/devices/bulk-import`

---

## Next Steps
- Implement frontend bulk import page and button.
- Add integration tests for UI flow.
