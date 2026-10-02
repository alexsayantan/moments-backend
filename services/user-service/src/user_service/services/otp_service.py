import enum
import hmac
import logging
import secrets

from fastapi import HTTPException, status

from user_service.core.config import settings
from user_service.services.redis_service import RedisService, redis_service

logger = logging.getLogger(__name__)


class OtpPurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


class OtpService:
    """Dedicated service for generating, saving, and validating OTPs backed by Redis with TTL."""

    def __init__(self, redis_srv: RedisService | None = None) -> None:
        self.redis = redis_srv or redis_service

    def _get_otp_key(self, purpose: str, email: str) -> str:
        return f"otp:{purpose}:{email.lower().strip()}"

    def _get_attempts_key(self, purpose: str, email: str) -> str:
        return f"otp_attempts:{purpose}:{email.lower().strip()}"

    def _get_cooldown_key(self, purpose: str, email: str) -> str:
        return f"otp_cooldown:{purpose}:{email.lower().strip()}"

    def generate_otp(self, length: int | None = None) -> str:
        """Generate a cryptographically secure numeric OTP."""
        otp_len = length or settings.otp_length
        range_start = 10 ** (otp_len - 1)
        range_end = (10**otp_len) - 1
        return str(secrets.randbelow(range_end - range_start + 1) + range_start)

    def create_and_send_otp(
        self,
        email: str,
        purpose: OtpPurpose | str,
        ttl_seconds: int | None = None,
    ) -> str:
        """Generate OTP, persist to Redis with TTL, reset attempts counter, and dispatch via email."""
        purpose_str = purpose.value if isinstance(purpose, OtpPurpose) else str(purpose)
        email_clean = email.lower().strip()
        ttl = ttl_seconds or settings.otp_expire_seconds

        # Check rate-limiting cooldown between resend requests
        cooldown_key = self._get_cooldown_key(purpose_str, email_clean)
        if self.redis.exists(cooldown_key):
            remaining_cooldown = self.redis.get_ttl(cooldown_key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {max(1, remaining_cooldown)} seconds before requesting a new OTP.",
            )

        # Generate secure OTP
        otp = self.generate_otp()
        otp_key = self._get_otp_key(purpose_str, email_clean)
        attempts_key = self._get_attempts_key(purpose_str, email_clean)

        # Save OTP to Redis with TTL
        self.redis.set(otp_key, otp, ttl_seconds=ttl)
        # Reset attempt counter with same TTL
        self.redis.set(attempts_key, "0", ttl_seconds=ttl)
        # Set cooldown timer
        if settings.otp_resend_cooldown_seconds > 0:
            self.redis.set(cooldown_key, "1", ttl_seconds=settings.otp_resend_cooldown_seconds)

        # Dispatch email
        self._dispatch_email(email_clean, purpose_str, otp, ttl)

        return otp

    def verify_otp(
        self,
        email: str,
        purpose: OtpPurpose | str,
        provided_otp: str,
    ) -> bool:
        """Verify the provided OTP against the Redis record with brute-force protection."""
        purpose_str = purpose.value if isinstance(purpose, OtpPurpose) else str(purpose)
        email_clean = email.lower().strip()
        otp_key = self._get_otp_key(purpose_str, email_clean)
        attempts_key = self._get_attempts_key(purpose_str, email_clean)

        stored_otp = self.redis.get(otp_key)
        if not stored_otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired or was not requested. Please request a new OTP.",
            )

        # Increment attempts counter
        attempts = self.redis.increment(attempts_key)
        if attempts > settings.otp_max_attempts:
            # Invalidate OTP on repeated failed attempts to block brute force
            self.redis.delete(otp_key, attempts_key)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum OTP verification attempts exceeded. Please request a new OTP.",
            )

        # Constant-time comparison
        if not hmac.compare_digest(stored_otp, provided_otp.strip()):
            remaining = max(0, settings.otp_max_attempts - attempts)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP. {remaining} attempt(s) remaining.",
            )

        # Verification successful: remove OTP and attempts keys
        self.redis.delete(otp_key, attempts_key)
        return True

    def _dispatch_email(self, email: str, purpose: str, otp: str, ttl_seconds: int) -> None:
        """Simulate email dispatch (or publish event to notification queue)."""
        logger.info(
            "==================================================\n"
            "[EMAIL SERVICE MOCK] To: %s\n"
            "Purpose: %s\n"
            "OTP: %s\n"
            "Valid for: %d seconds (%d minutes)\n"
            "==================================================",
            email,
            purpose,
            otp,
            ttl_seconds,
            ttl_seconds // 60,
        )


otp_service = OtpService()
