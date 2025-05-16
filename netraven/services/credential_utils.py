"""Credential utility functions for universal credential access across NetRaven jobs and drivers."""

def get_device_password(device):
    """
    Universally retrieve the decrypted password from a device or credential object.
    - If the object has a .password property (not a method), use it (DeviceWithCredentials, etc.)
    - If the object has a .get_password property (not a method), use it (Credential model)
    - As a fallback, try to decrypt .password if present (for legacy or raw objects)
    """
    # Prefer .password property (used by DeviceWithCredentials and wrappers)
    if hasattr(device, "password"):
        pw = getattr(device, "password")
        if not callable(pw):
            return pw
    # Fallback: Credential model uses .get_password property
    if hasattr(device, "get_password"):
        pw = getattr(device, "get_password")
        if not callable(pw):
            return pw
    # As a last resort, try to decrypt .password if present
    from netraven.services.crypto import decrypt_password
    enc_pw = getattr(device, "password", None)
    if enc_pw:
        try:
            return decrypt_password(enc_pw)
        except Exception:
            return enc_pw  # fallback: return as-is if not decryptable
    return None
