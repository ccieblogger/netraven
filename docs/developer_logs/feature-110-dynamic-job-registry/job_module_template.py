"""
Job Module Template for NetRaven Dynamic Job Registry

- Filename (without .py) will be used as the unique job_type by the loader.
- Do NOT set job_type manually in JOB_META; it will be set automatically.
- Provide user-facing fields: label, description, icon, category, etc.
- Implement a run() function as the job handler.
"""

JOB_META = {
    "label": "<User-Friendly Job Name>",
    "description": "<Describe what this job does>",
    "icon": "<mdi-icon-name>",
    "category": "<job category>",
    "default_schedule": "<onetime|daily|weekly|...>",
    # Add any other UI/UX fields as needed
}

def run(device, job_id, config, db):
    """Main job logic. Implement the job here."""
    # ...job logic...
    return {"success": True, "details": "Job completed."} 