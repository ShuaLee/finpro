"""
users.models.profile
~~~~~~~~~~~~~~~~~~~~
Defines the Profile model, which extends user functionality with additional fields.
"""

from django.conf import settings
from django.db import models
from common.utils.country_data import (
    get_country_choices, get_currency_choices,
    validate_country_code, validate_currency_code
)


class Profile(models.Model):
    """
    Extended user details for personalization and subscription management.

    - Basic identity (optional): first_name, last_name, birth_date
    - Preferences: language, preferred_currency, country
    - Business logic: plan, account_type, email preferences
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Basic identity info
    full_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Preferences
    language = models.CharField(max_length=30, blank=False, default="en")
    country = models.CharField(
        max_length=2,
        choices=get_country_choices(),
        validators=[validate_country_code],
        default="US"
    )
    preferred_currency = models.CharField(
        max_length=3,
        choices=get_currency_choices(),
        validators=[validate_currency_code],
        default="USD"
    )

    # Subscriptions
    plan = models.ForeignKey(
        'subscriptions.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        help_text="The subscription plan associated with this profile."
    )
    account_type = models.ForeignKey(
        'subscriptions.AccountType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
        help_text="The account type for this user (e.g., Individual, Manager)."
    )

    # Notifications
    receive_email_updates = models.BooleanField(default=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

    @property
    def first_name(self):
        """
        Extract the first word of full_name for personalization.
        Returns 'there' if full_name is missing or blank.
        """
        if self.full_name and self.full_name.strip():
            return self.full_name.strip().split()[0]
        return "there"

    def save(self, *args, **kwargs):
        """
        Override save to enforce uppercase currency codes.
        """
        if self.preferred_currency:
            self.preferred_currency = self.preferred_currency.upper()
        super().save(*args, **kwargs)
