"""Credential utility functions for universal credential access across NetRaven jobs and drivers."""

from netraven.services.crypto import decrypt_password

def get_device_password(device):
    """
    Universally retrieve the decrypted password from a device or credential object.
    - If the object has a .get_password property (property or method), use it (Credential model)
    - If the object has a .password property (not a method), always try to decrypt it (DeviceWithCredentials, etc.)
    - As a fallback, try to decrypt .password if present (for legacy or raw objects)
    """
    # Prefer .get_password property (property or method)
    if hasattr(device, "get_password"):
        val = getattr(device, "get_password")
        # If it's a method, call it
        if callable(val):
            return val()
        # If it's a property, return its value
        return val
    # Next, try .password property (not a method)
    if hasattr(device, "password"):
        pw = getattr(device, "password")
        if not callable(pw) and pw is not None:
            try:
                return decrypt_password(pw)
            except Exception:
                return pw  # fallback: return as-is if not decryptable
        return pw
    return None
