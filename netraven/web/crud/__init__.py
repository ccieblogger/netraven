"""
CRUD operations for the NetRaven web interface.

This package contains database operations for creating, reading, updating, and
deleting records, as well as other database manipulation functions.
"""

# Import CRUD operations from submodules
from netraven.web.crud.user import get_user, get_users, get_user_by_email, get_user_by_username, create_user, update_user, delete_user, update_user_last_login
from netraven.web.crud.device import get_device, get_devices, create_device, update_device, delete_device, update_device_backup_status
from netraven.web.crud.backup import get_backup, get_backups, create_backup, delete_backup, get_backup_content

# Import tag CRUD operations
from netraven.web.crud.tag import (
    get_tags, get_tag, get_tag_by_name, create_tag, update_tag, delete_tag,
    get_tags_for_device, get_devices_for_tag, add_tag_to_device, remove_tag_from_device,
    bulk_add_tags_to_devices, bulk_remove_tags_from_devices
)

# Import tag rule CRUD operations
from netraven.web.crud.tag_rule import (
    get_tag_rules, get_tag_rule, create_tag_rule, update_tag_rule, delete_tag_rule,
    apply_rule, test_rule
)

# Import job log CRUD operations
from netraven.web.crud.job_log import (
    get_job_logs, get_job_log, get_job_log_entries, get_job_log_with_entries,
    get_job_log_with_details, delete_job_log, delete_old_job_logs,
    delete_job_logs_by_retention_policy
)

# Import scheduled job CRUD operations
from netraven.web.crud.scheduled_job import (
    get_scheduled_jobs, get_scheduled_job, get_scheduled_job_with_details,
    create_scheduled_job, update_scheduled_job, delete_scheduled_job,
    toggle_scheduled_job, update_job_last_run, get_due_jobs
)

# Import credential CRUD operations
from netraven.web.crud.credential import (
    get_credentials, get_credential, create_credential, update_credential, delete_credential,
    get_credentials_by_tag, associate_credential_with_tag, remove_credential_from_tag,
    test_credential, bulk_associate_credentials_with_tags, bulk_remove_credentials_from_tags,
    get_credential_stats
)

# Import admin settings CRUD operations
from netraven.web.crud.admin_settings import (
    get_admin_setting, get_admin_setting_by_key, get_admin_settings,
    get_admin_settings_by_category, create_admin_setting, update_admin_setting,
    update_admin_setting_value, delete_admin_setting, initialize_default_settings
) 