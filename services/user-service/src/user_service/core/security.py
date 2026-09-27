from pwdlib import PasswordHash

# Initialize Argon2id password hasher (recommended by OWASP and modern security standards)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    return password_hash.verify(plain_password, hashed_password)
