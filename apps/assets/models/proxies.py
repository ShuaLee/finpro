from assets.models.assets import Asset
from core.types import DomainType


class EquityAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Equity"
        verbose_name_plural = "Equities"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.EQUITY
        super().save(*args, **kwargs)


class BondAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Bond"
        verbose_name_plural = "Bonds"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.BOND
        super().save(*args, **kwargs)


class CryptoAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Crypto"
        verbose_name_plural = "Cryptos"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.CRYPTO
        super().save(*args, **kwargs)


class MetalAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Metal"
        verbose_name_plural = "Metals"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.METAL
        super().save(*args, **kwargs)


class RealEstateAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Real Estate"
        verbose_name_plural = "Real Estate"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.REAL_ESTATE
        super().save(*args, **kwargs)


class CustomAsset(Asset):
    class Meta:
        proxy = True
        verbose_name = "Custom Asset"
        verbose_name_plural = "Custom Assets"

    def save(self, *args, **kwargs):
        self.asset_type = DomainType.CUSTOM
        super().save(*args, **kwargs)
