"""
Field mappings for FMP → CryptoDetail model.
Keeps fetchers clean and allows easy provider swaps.
"""

# ------------------------------
# Profile mapping
# ------------------------------
CRYPTO_PROFILE_MAP = {
    "description": "description",
    "website": "website",
    "image": "logo_url",
    "exchange": "exchange",
}

# ------------------------------
# Quote mapping
# ------------------------------
CRYPTO_QUOTE_MAP = {
    "price": "last_price",
    "currency": "currency",
    "marketCap": "market_cap",
    "volume": "volume_24h",
    "circulatingSupply": "circulating_supply",
    "sharesOutstanding": "total_supply",
    "dayHigh": "day_high",
    "dayLow": "day_low",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "open": "open_price",
    "previousClose": "previous_close",
    "changesPercentage": "changes_percentage",
    # Decimals not provided by FMP → default handled in fetchers
}
