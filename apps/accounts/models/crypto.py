from django.db import models
from accounts.models.base import BaseAccount
from portfolios.models.subportfolio import SubPortfolio


class CryptoAccount(BaseAccount):
    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name="crypto_wallets"
    )

    asset_type = "crypto"
    account_variant = "crypto_wallet"

    class Meta:
        verbose_name = "Crypto Wallet"
        constraints = [
            models.UniqueConstraint(
                fields=["subportfolio", "name"],
                name="unique_cryptowallet_name_in_subportfolio"
            )
        ]

    @property
    def active_schema(self):
        """
        Get the active schema for this crypto account by asking the
        subportfolio for its schema mapped to this account variant.
        """
        return self.subportfolio.get_schema_for_account_model("crypto_wallet")
