from django.conf import settings
from django.db import models


class Profile(models.Model):
    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    full_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    language = models.CharField(max_length=16, default="en")
    timezone = models.CharField(max_length=64, default="UTC")

    country = models.ForeignKey(
        "fx.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )

    # Required base valuation currency for the user
    currency = models.ForeignKey(
        "fx.FXCurrency",
        null=False,
        blank=False,
        on_delete=models.PROTECT,
        related_name="profiles",
    )

    # Keep these here for now if your subscription model is profile-scoped
    plan = models.ForeignKey(
        "subscriptions.Plan",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )
    account_type = models.ForeignKey(
        "subscriptions.AccountType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )

    receive_email_updates = models.BooleanField(default=True)
    receive_marketing_emails = models.BooleanField(default=False)

    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NOT_STARTED,
    )
    onboarding_step = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.user.email
