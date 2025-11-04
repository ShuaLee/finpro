from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account_classification import AccountClassification

from core.types import (
    get_account_type_choices,
    get_domain_for_account_type,
    get_domain_meta,
)


class Account(models.Model):
    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="accounts"
    )
    name = models.CharField(max_length=100)

    account_type = models.CharField(
        max_length=50,
        db_index=True,
        choices=get_account_type_choices(),
    )

    broker = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Broker name (only used for brokered accounts such as equity or crypto)."
    )

    classification = models.ForeignKey(
        AccountClassification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts",
        help_text="User-specific classification (e.g., TFSA, RRSP, 401k)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "account_type", "name"],
                name="uniq_account_name_in_portfolio_per_type",
            )
        ]
        ordering = ["portfolio", "name"]

    def __str__(self):
        return f"{self.name} ({self.account_type})"

    # ----------------------------
    # Domain Helpers
    # ----------------------------
    @property
    def domain_type(self) -> str:
        """Resolve domain (equity, crypto, etc.) from account_type."""
        return get_domain_for_account_type(self.account_type)

    @property
    def profile(self):
        return self.portfolio.profile

    @property
    def currency(self):
        return self.profile.currency

    # ----------------------------
    # Validation
    # ----------------------------
    def clean(self):
        """
        Ensure account_type is valid for the domain,
        enforce domain-specific restrictions,
        and validate classification ownership.
        """
        domain = self.domain_type
        domain_meta = get_domain_meta(domain)
        allowed_types = domain_meta.get("account_types", [])

        # 1. Account type must belong to its domain
        if self.account_type not in allowed_types:
            raise ValidationError(
                f"Account type '{self.account_type}' is not valid for domain '{domain}'. "
                f"Allowed: {allowed_types}"
            )

        # 2. Domain-specific restrictions
        if domain == "crypto" and self.broker:
            raise ValidationError("Crypto wallets should not have a broker.")
        if domain == "real_estate" and self.broker:
            raise ValidationError(
                "Real estate accounts should not have a broker.")

        # 3. Classification must belong to same profile
        if self.classification and self.classification.profile != self.profile:
            raise ValidationError(
                f"Classification '{self.classification}' does not belong to this account's profile."
            )

        super().clean()

    def save(self, *args, **kwargs):
        """
        Override save to ensure that when a new Account is created,
        it is properly initialized with its classification and schema.
        Initialization only runs once classification is already linked.
        """
        is_new = self._state.adding

        # Run model validation before saving
        self.full_clean()
        super().save(*args, **kwargs)

        # 🧩 Only initialize if classification already exists (prevents admin race)
        if is_new and self.classification and getattr(self.classification, "definition", None):
            from accounts.services.account_service import AccountService

            AccountService.initialize_account(
                self,
                self.classification.definition,
                self.portfolio.profile
            )

    # ----------------------------
    # Schema Binding
    # ----------------------------

    @property
    def active_schema(self):
        """
        Return the schema associated with this account’s portfolio and account_type.
        Each portfolio has one schema per account type.
        """
        from schemas.models.schema import Schema

        schema = Schema.objects.filter(
            portfolio=self.portfolio,
            account_type=self.account_type
        ).first()

        if not schema:
            # You can choose to raise instead if missing schemas are always a bug
            # raise RuntimeError(f"No schema found for account type '{self.account_type}' in portfolio {self.portfolio.id}.")
            return None

        return schema
