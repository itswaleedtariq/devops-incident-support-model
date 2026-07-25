"""Tests for JWT encoding, decoding, and expiry semantics."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.core.jwt import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestJWTEncoding:
    def test_access_token_is_string(self) -> None:
        token = create_access_token(subject=str(uuid.uuid4()))
        assert isinstance(token, str) and token.count(".") == 2

    def test_refresh_token_is_string(self) -> None:
        token = create_refresh_token(subject=str(uuid.uuid4()))
        assert isinstance(token, str) and token.count(".") == 2

    def test_access_and_refresh_differ(self) -> None:
        sub = str(uuid.uuid4())
        assert create_access_token(sub) != create_refresh_token(sub)


class TestJWTDecoding:
    def test_decode_valid_access_token(self) -> None:
        sub = str(uuid.uuid4())
        token = create_access_token(subject=sub)
        payload = decode_token(token)
        assert payload["sub"] == sub
        assert payload["type"] == ACCESS_TOKEN_TYPE

    def test_decode_valid_refresh_token(self) -> None:
        sub = str(uuid.uuid4())
        token = create_refresh_token(subject=sub)
        payload = decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
        assert payload["type"] == REFRESH_TOKEN_TYPE

    def test_decode_wrong_type_raises(self) -> None:
        access = create_access_token(subject=str(uuid.uuid4()))
        with pytest.raises(JWTError):
            decode_token(access, expected_type=REFRESH_TOKEN_TYPE)

    def test_decode_malformed_token_raises(self) -> None:
        with pytest.raises(JWTError):
            decode_token("not.a.valid.jwt")

    def test_decode_expired_token_raises(self) -> None:
        expired = create_access_token(
            subject=str(uuid.uuid4()),
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(JWTError):
            decode_token(expired)

    def test_extra_claims_are_included(self) -> None:
        sub = str(uuid.uuid4())
        token = create_access_token(subject=sub, extra_claims={"role": "Admin"})
        payload = decode_token(token)
        assert payload["role"] == "Admin"

    def test_jti_is_unique_per_token(self) -> None:
        sub = str(uuid.uuid4())
        t1 = create_access_token(subject=sub)
        t2 = create_access_token(subject=sub)
        p1, p2 = decode_token(t1), decode_token(t2)
        assert p1["jti"] != p2["jti"]
