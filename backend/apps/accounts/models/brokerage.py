from django.core.exceptions import ValidationError
from django.db import models


class BrokerageConnection(models.Model):
    class SourceType(models.TextChoices):
        BROKERAGE = "brokerage", "Brokerage"
        CRYPTO_EXCHANGE = "crypto_exchange", "Crypto Exchange"
        WALLET = "wallet", "Wallet"

    class Provider(models.TextChoices):
        MANUAL = "manual", "Manual"
        PLAID = "plaid", "Plaid"
        ALPACA = "alpaca", "Alpaca"
        COINBASE = "coinbase", "Coinbase"
        KRAKEN = "kraken", "Kraken"
        WALLET_CONNECT = "wallet_connect", "Wallet Connect"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ERROR = "error", "Error"
        DISCONNECTED = "disconnected", "Disconnected"

    account = models.OneToOneField(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="brokerage_connection",
    )
    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.BROKERAGE,
    )
    provider = models.CharField(max_length=30, choices=Provider.choices)
    external_account_id = models.CharField(max_length=255, null=True, blank=True)

    # Opaque reference to provider-side token material.
    # Do not store raw broker/exchange secrets in this app database.
    access_token_ref = models.CharField(max_length=255, null=True, blank=True)

    # Stored read-only scopes granted by the end user.
    scopes = models.JSONField(default=list, blank=True)

    connection_label = models.CharField(max_length=255, null=True, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    consent_expires_at = models.DateTimeField(null=True, blank=True)

    # Legacy field kept for backward compatibility during migration.
    # Avoid using for any credential data.
    credentials = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.account.name} [{self.provider}]"

    @property
    def has_holdings_read_scope(self) -> bool:
        wanted = {"holdings.read", "positions.read", "balances.read"}
        granted = set(self.scopes or [])
        return any(scope in granted for scope in wanted)

    def clean(self):
        super().clean()
        if not self.pk:
            return

        original = BrokerageConnection.objects.select_related("account").only("account").filter(pk=self.pk).first()
        if original and original.account.pk != self.account.pk:
            raise ValidationError("Connection account cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
