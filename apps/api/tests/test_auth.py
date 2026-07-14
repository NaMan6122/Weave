import time

import pytest
from jose import jwt, JWTError

from app.config import settings
from app.services.auth import AuthService


class TestApiKey:
    def test_generate_api_key_format(self):
        raw_key, hashed = AuthService.generate_api_key()
        assert raw_key.startswith("wv_live_")
        # 8 prefix chars + 64 hex chars = 72
        assert len(raw_key) == 72

    def test_generate_api_key_uniqueness(self):
        key1, _ = AuthService.generate_api_key()
        key2, _ = AuthService.generate_api_key()
        assert key1 != key2

    def test_hash_api_key_deterministic(self):
        key = "wv_live_abc123"
        assert AuthService.hash_api_key(key) == AuthService.hash_api_key(key)

    def test_hash_api_key_different_inputs(self):
        assert AuthService.hash_api_key("key_a") != AuthService.hash_api_key("key_b")

    def test_hash_api_key_is_hex(self):
        h = AuthService.hash_api_key("wv_live_test")
        assert len(h) == 64
        int(h, 16)  # should not raise


class TestJwt:
    def test_create_and_decode_roundtrip(self):
        token = AuthService.create_jwt("user-123", "test@example.com")
        payload = AuthService.decode_jwt(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_decode_invalid_token_raises(self):
        with pytest.raises(JWTError):
            AuthService.decode_jwt("not.a.valid.token")

    def test_decode_expired_token_raises(self):
        payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "exp": int(time.time()) - 3600,
        }
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        with pytest.raises(JWTError):
            AuthService.decode_jwt(token)
