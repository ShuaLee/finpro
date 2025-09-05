from django.db import models
from portfolios.models.subportfolio import SubPortfolio
from .base import BaseAccount


class MetalAccount(BaseAccount):
    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name='storage_facilities'
    )

    asset_type = "metal"
    account_variant = "storage_facility"

    class Meta:
        verbose_name = "Storage Facility"
        constraints = [
            models.UniqueConstraint(
                fields=["subportfolio", "name"],
                name="unique_storagefacility_name_in_subportfolio"
            )
        ]

    @property
    def active_schema(self):
        """
        Get the active schema for this metal account by asking the
        subportfolio for its schema mapped to this account variant.
        """
        return self.subportfolio.get_schema_for_account_model("storage_facility")
