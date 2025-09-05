from django.db import models

class AccountType(models.TextChoices):
    STOCK_SELF_MANAGED = "stock_self", "Self-Managed Stock"
    STOCK_MANAGED = "stock_managed", "Managed Stock"
    CRYPTO_WALLET = "crypto_wallet", "Crypto Wallet"
    METAL_STORAGE = "metal_storage", "Metal Storage"
    CUSTOM = "custom", "Custom Account"