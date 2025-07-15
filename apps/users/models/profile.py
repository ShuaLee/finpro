"""
users.models.profile
~~~~~~~~~~~~~~~~~~~~
Defines the Profile model, which extends user functionality with additional fields.
"""

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """
    Stores additional details about a user that are not part of authentication.

    Fields:
        account_type (str): Individual or manager.
        plan (str): Subscription tier (Free, Premium).
        language (str): Preferred language.
        currency (str): Preferred currency code.
        theme (str): UI theme preference.
        is_asset_manager (bool): Indicates if user manages assets for others.
        receive_email_updates (bool): Email subscription preference.
    """

    ACCOUNT_TYPES = [
        ('individual', 'Individual'),
        ('manager', 'Manager'),
    ]
    PLAN_TIERS = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPES, default='individual')
    plan = models.CharField(max_length=20, choices=PLAN_TIERS, default='free')
    language = models.CharField(max_length=30, blank=False, default="en")
    currency = models.CharField(
        max_length=3,
        choices=settings.CURRENCY_CHOICES,
        blank=False,
        default="USD"
    )
    theme = models.CharField(
        max_length=10, choices=THEME_CHOICES, default='system')
    is_asset_manager = models.BooleanField(default=False)
    receive_email_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

    def save(self, *args, **kwargs):
        """
        Override save to enforce uppercase currency codes.
        """
        self.currency = self.currency.upper()
        super().save(*args, **kwargs)
