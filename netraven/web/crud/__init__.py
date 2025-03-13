"""
CRUD operations for the NetRaven web interface.

This package contains database operations for creating, reading, updating, and
deleting records, as well as other database manipulation functions.
"""

# Import CRUD operations from submodules
from netraven.web.crud.user import get_user, get_user_by_email, get_user_by_username, create_user, update_user, delete_user, update_user_last_login
from netraven.web.crud.device import get_device, get_devices, create_device, update_device, delete_device, update_device_backup_status
from netraven.web.crud.backup import get_backup, get_backups, create_backup, delete_backup

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