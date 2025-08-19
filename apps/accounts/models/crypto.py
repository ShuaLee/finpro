from django.db import models
from accounts.models.base import BaseAccount
from portfolios.models.crypto import CryptoPortfolio

class CryptoWallet(BaseAccount):
    crypto_portfolio = models.ForeignKey(
        CryptoPortfolio,
        on_delete=models.CASCADE,
        related_name='crypto_wallets'
    )

    asset_type = "crypto"

    account_variant = "crypto_wallet"

    class Meta:
        verbose_name = "Crypto Wallet"
        constraints = [
            models.UniqueConstraint(
                fields=['crypto_portfolio', 'name'],
                name='unique_cryptowallet_name_in_portfolio'
            )
        ]

    @property
    def sub_portfolio(self):
        return self.crypto_portfolio
    
    @property
    def active_schema(self):
        return self.crypto_portfolio.get_schema_for_account_model("crypto_wallet")