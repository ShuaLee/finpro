from django.db import models


class ActiveEquityListing(models.Model):
    provider = models.CharField(max_length=50, default="fmp")
    symbol = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    source_payload = models.JSONField(default=dict, blank=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [
            models.Index(fields=["provider", "symbol"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class ActiveCryptoListing(models.Model):
    provider = models.CharField(max_length=50, default="fmp")
    symbol = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    base_symbol = models.CharField(max_length=20, blank=True)
    quote_currency = models.CharField(max_length=10, blank=True)
    source_payload = models.JSONField(default=dict, blank=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [
            models.Index(fields=["provider", "symbol"]),
            models.Index(fields=["base_symbol"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class ActiveCommodityListing(models.Model):
    provider = models.CharField(max_length=50, default="fmp")
    symbol = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=100, blank=True)
    trade_month = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    source_payload = models.JSONField(default=dict, blank=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [
            models.Index(fields=["provider", "symbol"]),
            models.Index(fields=["name"]),
            models.Index(fields=["exchange"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class FXRateCache(models.Model):
    provider = models.CharField(max_length=50, default="fmp")
    base_currency = models.CharField(max_length=10)
    quote_currency = models.CharField(max_length=10)
    pair_symbol = models.CharField(max_length=30)
    rate = models.DecimalField(max_digits=30, decimal_places=10)
    source_payload = models.JSONField(default=dict, blank=True)
    as_of = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["base_currency", "quote_currency"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "base_currency", "quote_currency"],
                name="uniq_fx_rate_cache_per_provider_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["provider", "base_currency", "quote_currency"]),
            models.Index(fields=["pair_symbol"]),
        ]

    def __str__(self):
        return f"{self.base_currency}/{self.quote_currency}={self.rate}"
