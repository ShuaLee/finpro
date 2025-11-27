"""
users.models.profile
~~~~~~~~~~~~~~~~~~~~
Defines the Profile model, which extends user functionality with additional fields.
"""

from django.conf import settings
from django.db import models, transaction
from common.utils.country_currency_catalog import get_common_country_choices
from fx.models import FXCurrency


class ProfileManager(models.Manager):
    def with_plan(self, slug):
        return self.filter(plan__slug=slug)

    def for_user(self, user):
        return self.get(user=user)


class Profile(models.Model):
    """
    Extended user details for personalization and subscription management.

    Fields:
    - Identity: full_name (optional now, may be required for KYC later)
    - Preferences: language, preferred_currency (default USD), country (optional)
    - Subscriptions: plan, account_type
    - Notifications: email updates
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # Basic identity info
    full_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Preferences
    language = models.CharField(max_length=30, blank=False, default="en")
    country = models.CharField(
        max_length=2,
        choices=get_common_country_choices(),
        blank=True,  # ✅ optional for now
        null=True,
    )
    currency = models.ForeignKey(
        FXCurrency,
        on_delete=models.PROTECT,
        related_name="profiles",
        null=True,
        blank=False,     # required
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
        super().save(*args, **kwargs)
