from django.db import models
from django.core.exceptions import ValidationError

from accounts.models.account_type import AccountType
from assets.models.core import AssetType


class Account(models.Model):
    class PositionMode(models.TextChoices):
        MANUAL = "manual", "Manual"
        SYNCED = "synced", "Synced"
        LEDGER = "ledger", "Ledger"
        HYBRID = "hybrid", "Hybrid"

    portfolio = models.ForeignKey(
        "portfolios.Portfolio",
        on_delete=models.CASCADE,
        related_name="accounts",
    )

    name = models.CharField(max_length=100)

    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="accounts",
        help_text="The type of account (brokerage, crypto wallet, real estate container, etc.)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    position_mode = models.CharField(
        max_length=20,
        choices=PositionMode.choices,
        default=PositionMode.MANUAL,
        help_text="How holdings are maintained for this account.",
    )
    allow_manual_overrides = models.BooleanField(
        default=True,
        help_text="Whether users can manually adjust holdings when account is synced.",
    )
    schema = models.ForeignKey(
        "schemas.Schema",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accounts",
        help_text="Optional account-level schema override.",
    )
    allowed_asset_types = models.ManyToManyField(
        AssetType,
        blank=True,
        related_name="accounts_with_restrictions",
        help_text="Optional account-level supported asset types. Leave empty to allow all asset types.",
    )
    enforce_restrictions = models.BooleanField(
        default=False,
        help_text="Whether supported asset types should be treated as a hard rule instead of guidance.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "account_type", "name"],
                name="uniq_account_name_in_portfolio_per_type",
            )
        ]
        ordering = ["portfolio", "name"]

    def __str__(self):
        return f"{self.name} [{self.account_type.slug}]"

    # ---------- Convenience ----------

    @property
    def profile(self):
        return self.portfolio.profile

    @property
    def currency(self):
        return self.profile.currency

    # ---------- Validation ----------
    def clean(self):
        super().clean()

        if self.pk:
            original = Account.objects.select_related("portfolio").only("portfolio").filter(pk=self.pk).first()
            if original and original.portfolio.pk != self.portfolio.pk:
                raise ValidationError("Account owner portfolio cannot be changed.")

        # No broker rules - always optional

    # ---------- Save ----------
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        self.full_clean()
        super().save(*args, **kwargs)
        if is_new and not self.allowed_asset_types.exists():
            default_asset_type_ids = list(self.account_type.allowed_asset_types.values_list("id", flat=True))
            if default_asset_type_ids:
                self.allowed_asset_types.set(default_asset_type_ids)

    def has_asset_type_restrictions(self):
        return self.allowed_asset_types.exists()

    def is_asset_type_allowed(self, asset_type):
        if asset_type is None:
            return True
        if not self.has_asset_type_restrictions():
            return True
        return self.allowed_asset_types.filter(pk=asset_type.pk).exists()

    @property
    def supported_asset_types(self):
        return self.allowed_asset_types

    def has_supported_asset_types(self):
        return self.has_asset_type_restrictions()

    def supports_asset_type(self, asset_type):
        return self.is_asset_type_allowed(asset_type)

    # ---------- Schema ----------

    def resolve_schema_for_asset_type(self, asset_type=None):
        from django.apps import apps

        try:
            Schema = apps.get_model("schemas", "Schema")
        except (LookupError, ValueError):
            return None

        if self.schema is not None:
            return self.schema

        if asset_type is not None:
            schema = Schema.objects.filter(
                portfolio=self.portfolio,
                asset_type=asset_type,
            ).first()
            if schema:
                return schema

        # Legacy fallback while older account-type-scoped schemas still exist.
        return Schema.objects.filter(
            portfolio=self.portfolio,
            account_type=self.account_type,
            asset_type__isnull=True,
        ).first()

    @property
    def active_schema(self):
        if self.schema is not None:
            return self.schema

        allowed_asset_types = list(self.allowed_asset_types.all()[:2])
        if len(allowed_asset_types) == 1:
            return self.resolve_schema_for_asset_type(allowed_asset_types[0])

        return self.resolve_schema_for_asset_type(None)
