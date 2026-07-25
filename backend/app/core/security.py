"""
Password hashing utilities.

Uses ``passlib`` with the ``bcrypt`` scheme.  Bcrypt is deliberately slow
(work factor configurable via ``BCRYPT_ROUNDS``) to make brute-force attacks
computationally expensive even if the password hash database is leaked.

Never store plain-text passwords.  Always call :func:`hash_password` before
persisting and :func:`verify_password` for verification.
"""

from __future__ import annotations

from passlib.context import CryptContext

from app.config.settings import settings

# ``deprecated="auto"`` will mark any hash produced by a non-current
# scheme as needing rehash — enabling seamless algorithm upgrades.
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(plain_password: str) -> str:
    """
    Return the bcrypt hash of *plain_password*.

    The salt is generated automatically by passlib and embedded in the hash.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify *plain_password* against a stored *password_hash*.

    Returns ``False`` (never raises) on malformed hashes.
    """
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except (ValueError, TypeError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """
    Return ``True`` if *password_hash* uses an outdated scheme or work factor.

    Application logic can call this on successful login to transparently
    upgrade the stored hash without user interaction.
    """
    return _pwd_context.needs_update(password_hash)
