from django.db import models


class AuthEvent(models.Model):
    class EventType(models.TextChoices):
        REGISTERED = "registered", "Registered"
        LOGIN_SUCCEEDED = "login_succeeded", "Login Succeeded"
        LOGIN_FAILED = "login_failed", "Login Failed"
        ACCOUNT_LOCKED = "account_locked", "Account Locked"
        LOGOUT = "logout", "Logout"
        PASSWORD_CHANGED = "password_changed", "Password Changed"
        PASSWORD_RESET_REQUESTED = "password_reset_requested", "Password Reset Requested"
        PASSWORD_RESET_COMPLETED = "password_reset_completed", "Password Reset Completed"
        EMAIL_VERIFICATION_SENT = "email_verification_sent", "Email Verification Sent"
        EMAIL_VERIFIED = "email_verified", "Email Verified"
        EMAIL_CHANGE_REQUESTED = "email_change_requested", "Email Change Requested"
        EMAIL_CHANGED = "email_changed", "Email Changed"
        TRUSTED_DEVICE_ADDED = "trusted_device_added", "Trusted Device Added"
        TRUSTED_DEVICE_REVOKED = "trusted_device_revoked", "Trusted Device Revoked"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="auth_events",
    )
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "event_type", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email}:{self.event_type}:{self.created_at}"
