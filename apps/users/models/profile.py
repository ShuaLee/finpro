"""
users.models.profile
~~~~~~~~~~~~~~~~~~~~
Defines the Profile model, which extends user functionality with additional fields.
"""

from django.conf import settings
from django.db import models
import pycountry

CURRENCY_CHOICES = [
    (currency.alpha_3, currency.name)
    for currency in pycountry.currencies
]

COUNTRY_CHOICES = [
    (country.alpha_2, country.name)  # alpha_2 for compact storage
    for country in pycountry.countries
]


class Profile(models.Model):
    """
    Stores additional details about a user that are not part of authentication.

    Fields:
        account_type (str): Individual or manager.
        plan (str): Subscription tier (Free, Premium).
        language (str): Preferred language.
        country (str): User's country.
        preferred_currency (str): Preferred currency code.
        birth_date (date): Optional user-provided birth date.
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

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_TIERS, default='free')
    language = models.CharField(max_length=30, blank=False, default="en")
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES, default="US")
    preferred_currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default="USD")
    birth_date = models.DateField(blank=True, null=True)
    account_type = models.CharField(max_length=50, null=True, blank=True) # Null / Blank for now to compensate for future expansion. - account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='individual')
    receive_email_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email

    def save(self, *args, **kwargs):
        """
        Override save to enforce uppercase currency codes.
        """
        if self.preferred_currency:
            self.preferred_currency = self.preferred_currency.upper()
        super().save(*args, **kwargs)
