from django.db import models
from django.utils import timezone


class EmailVerificationToken(models.Model):
    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Verify Email"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices,
        default=Purpose.VERIFY_EMAIL,
    )

    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "purpose", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.email}:{self.purpose}:{self.created_at}"

    @property
    def is_consumed(self):
        return self.consumed_at is not None

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_consumed and not self.is_expired