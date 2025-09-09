from django.core.exceptions import ValidationError
from django.db import models
from core.types import get_domain_for_account_type
from accounts.services.detail_model_resolver import get_domain_meta_with_details
from portfolios.models.subportfolio import SubPortfolio


class Account(models.Model):
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
        domain = self.subportfolio.type
        domain_meta = get_domain_meta_with_details(domain)
        allowed = domain_meta.get("account_types", [])

        if self.account_type not in allowed:
            raise ValidationError(
                f"Account type '{self.account_type}' is not valid for "
                f"subportfolio type '{domain}'. "
                f"Allowed: {allowed}"
            )

    def __str__(self):
        return f"{self.account_type} ({self.name})"

    @property
    def domain_type(self):
        """Resolve domain (stock, crypto, etc.) for this account_type."""
        return get_domain_for_account_type(self.account_type)

    @property
    def profile(self):
        return self.subportfolio.portfolio.profile

    @property
    def currency(self):
        return self.profile.currency

    @property
    def active_schema(self):
        from schemas.models import Schema
        try:
            return Schema.objects.get(
                subportfolio=self.subportfolio,
                account_type=self.account_type,
            )
        except Schema.DoesNotExist:
            return None