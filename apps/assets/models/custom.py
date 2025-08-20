from django.db import models
from accounts.models.custom import CustomAccount
from schemas.models.schema import SchemaColumn, SchemaColumnValue
from assets.models.base import AssetHolding


class CustomHolding(AssetHolding):
    """
    A user's owned item within a CustomAccount.
    MVP: keep everything SCV-backed; no CustomAsset model required yet.
    """
    account = models.ForeignKey(
        CustomAccount,
        on_delete=models.CASCADE,
        related_name='holdings'
    )

    # Optional friendly label for the item (backed by a holding-level 'title' column anyway)
    label = models.CharField(max_length=200, blank=True, null=True)

    # If I ever add a shared CustomAsset, I can FK it here.

    # --- Required abstract implementations ---
    @property
    def asset(self):
        # No separate asset model in MVP; treat the holding as the object
        return self
    
    def __str__(self):
        return self.label or f"Custom Holding #{self.id}"
    
    def get_asset_type(self):
        # Namespace with slug so logs/context can distinguish types
        return f"custom:{self.account.custom_portfolio.slug}"
    
    def get_active_schema(self):
        return self.account.active_schema

    def get_column_model(self):
        return SchemaColumn

    def get_column_value_model(self):
        return SchemaColumnValue

    def get_profile_currency(self):
        # If you use currency in formulas, pull from user’s profile
        return self.account.custom_portfolio.portfolio.profile.currency