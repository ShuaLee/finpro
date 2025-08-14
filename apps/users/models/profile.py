"""
users.models.profile
~~~~~~~~~~~~~~~~~~~~
Defines the Profile model, which extends user functionality with additional fields.
"""

from django.conf import settings
from django.db import models, transaction
from common.utils.country_currency_catalog import get_common_currency_choices, get_common_country_choices


class Profile(models.Model):
    """
    Extended user details for personalization and subscription management.

    - Basic identity (optional): first_name, last_name, birth_date
    - Preferences: language, preferred_currency, country
    - Business logic: plan, account_type, email preferences
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Profile check
    is_profile_complete = models.BooleanField(default=False)

    # Basic identity info
    full_name = models.CharField(max_length=150, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Preferences
    language = models.CharField(max_length=30, blank=False, default="en")
    country = models.CharField(
        max_length=2,
        choices=get_common_country_choices(),
        default="US"
    )
    currency = models.CharField(
        max_length=3,
        choices=get_common_currency_choices(),
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
        if self.currency:
            self.currency = self.currency.upper()

        old_currency = None
        if self.pk:
            try:
                old_currency = type(self).objects.only("currency").get(pk=self.pk).currency
            except type(self).DoesNotExist:
                old_currency = None

        super().save(*args, **kwargs)

        def _after_commit():
            # Keep accounts in sync (you already had this)
            from accounts.models.stocks import SelfManagedAccount
            SelfManagedAccount.objects.filter(
                stock_portfolio__portfolio__profile=self
            ).update(currency=self.currency)

            # If currency changed → recalc calculated SCVs for all holdings in this profile
            if old_currency and old_currency != self.currency:
                from schemas.services.recalc_triggers import recalc_holdings_for_profile
                recalc_holdings_for_profile(self)

        transaction.on_commit(_after_commit)

        from accounts.models.stocks import SelfManagedAccount
        SelfManagedAccount.objects.filter(
            stock_portfolio__portfolio__profile=self
        ).update(currency=self.currency)
