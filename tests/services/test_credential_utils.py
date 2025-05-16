import pytest
from netraven.services.credential_utils import get_device_password

class DummyDevice:
    def __init__(self, password=None, get_password=None):
        self.password = password
        if get_password is not None:
            self.get_password = get_password

class DummyCredential:
    @property
    def get_password(self):
        return "decrypted_from_property"

class DummyCredentialMethod:
    def get_password(self):
        return "decrypted_from_method"

def test_password_property():
    d = DummyDevice(password="plain_password")
    assert get_device_password(d) == "plain_password"

def test_get_password_property():
    c = DummyCredential()
    assert get_device_password(c) == "decrypted_from_property"

def test_get_password_method():
    c = DummyCredentialMethod()
    assert get_device_password(c) == "decrypted_from_method"

def test_decrypt_fallback(monkeypatch):
    # Simulate encrypted password fallback
    class Dummy:
        def __init__(self):
            self.password = "encrypted_pw"
    def fake_decrypt(val):
        assert val == "encrypted_pw"
        return "decrypted_pw"
    monkeypatch.setattr("netraven.services.credential_utils.decrypt_password", fake_decrypt)
    d = Dummy()
    assert get_device_password(d) == "decrypted_pw"

def test_none():
    class Dummy:
        pass
    d = Dummy()
    assert get_device_password(d) is None
