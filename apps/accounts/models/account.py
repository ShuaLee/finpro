from django.core.exceptions import ValidationError
from django.db import models
from core.types import DomainType, DOMAIN_TYPE_REGISTRY
from portfolios.models.subportfolio import SubPortfolio


class Account(models.Model):
    """
    Unified account model across all asset classes.

    - Every account belongs to a SubPortfolio.
    - Differentiated by `account_type` (e.g., stock_self, stock_managed).
    - `domain_type` is derived from the registry.
    - Extension tables hold special-case fields.
    """

    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name="accounts"
    )

    name = models.CharField(max_length=100)

    account_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Specific account type (e.g. stock_self, stock_managed, crypto_wallet)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subportfolio", "name"],
                name="uniq_account_name_in_subportfolio",
            )
        ]

    def clean(self):
        """
        Ensure account_type belongs to the subportfolio's domain.
        """
        domain_meta = DOMAIN_TYPE_REGISTRY.get(self.subportfolio.type, {})
        allowed = domain_meta.get("account_types", [])

        if self.type not in allowed:
            raise ValidationError(
                f"Account type '{self.type}' is not valid for "
                f"subportfolio type '{self.subportfolio.type}'. "
                f"Allowed: {allowed}"
            )

    def __str__(self):
        return f"{self.account_type} ({self.name})"

    # -------------------------------
    # Derived properties
    # -------------------------------
    @property
    def domain_type(self):
        """
        Resolve the domain (stock, crypto, etc.) for this account_type.
        """
        for domain, meta in DOMAIN_TYPE_REGISTRY.items():
            if self.account_type in meta.get("account_types", []):
                return domain
        return None

    @property
    def profile(self):
        return self.subportfolio.portfolio.profile

    @property
    def currency(self):
        return self.profile.currency

    @property
    def active_schema(self):
        from schemas.models import Schema  # avoid circular import
        try:
            return Schema.objects.get(
                subportfolio=self.subportfolio,
                account_type=self.account_type,
            )
        except Schema.DoesNotExist:
            return None
