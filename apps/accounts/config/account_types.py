SYSTEM_ACCOUNT_TYPES = [
    {
        "slug": "brokerage",
        "name": "Brokerage Account",
        "allows_multiple": True,
        "allowed_asset_types": ["equity", "bond"],
    },
    {
        "slug": "crypto_wallet",
        "name": "Crypto Wallet",
        "allows_multiple": True,
        "allowed_asset_types": ["crypto"],
    },
    {
        "slug": "real_estate_account",
        "name": "Real Estate Account",
        "allows_multiple": False,
        "allowed_asset_types": ["real_estate"],
    },
    {
        "slug": "custom_account",
        "name": "Custom Asset Container",
        "allows_multiple": True,
        "allowed_asset_types": ["custom"],
    },
]
