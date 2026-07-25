"""Tests for the password hashing/verification service."""

from __future__ import annotations

import pytest

from app.exceptions import WeakPasswordError
from app.services.password_service import PasswordService


class TestPasswordHashing:
    def test_hash_returns_non_empty_string(self) -> None:
        h = PasswordService.hash("Secret123!")
        assert isinstance(h, str) and len(h) > 20

    def test_hash_differs_from_plain(self) -> None:
        h = PasswordService.hash("Secret123!")
        assert h != "Secret123!"

    def test_verify_correct_password(self) -> None:
        h = PasswordService.hash("Secret123!")
        assert PasswordService.verify("Secret123!", h) is True

    def test_verify_wrong_password(self) -> None:
        h = PasswordService.hash("Secret123!")
        assert PasswordService.verify("WrongPass1!", h) is False

    def test_verify_malformed_hash_returns_false(self) -> None:
        assert PasswordService.verify("Secret123!", "not-a-hash") is False

    def test_two_hashes_of_same_password_differ(self) -> None:
        """Bcrypt uses per-hash salt — same input yields different hashes."""
        assert PasswordService.hash("Secret123!") != PasswordService.hash("Secret123!")


class TestPasswordStrength:
    def test_valid_password(self) -> None:
        PasswordService.validate_strength("Strong1!Password")  # must not raise

    def test_too_short(self) -> None:
        with pytest.raises(WeakPasswordError):
            PasswordService.validate_strength("Ab1!")

    def test_no_uppercase(self) -> None:
        with pytest.raises(WeakPasswordError):
            PasswordService.validate_strength("weakpass1!")

    def test_no_lowercase(self) -> None:
        with pytest.raises(WeakPasswordError):
            PasswordService.validate_strength("WEAKPASS1!")

    def test_no_digit(self) -> None:
        with pytest.raises(WeakPasswordError):
            PasswordService.validate_strength("WeakPass!")

    def test_no_special(self) -> None:
        with pytest.raises(WeakPasswordError):
            PasswordService.validate_strength("WeakPass1")
