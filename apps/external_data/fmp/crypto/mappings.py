"""
Field mappings for FMP → CryptoDetail model.
The FMP /quote endpoint contains both identity and quote data for crypto,
so we unify everything into a single map.
"""

# Most of these are not used as of right now, only the ones from quote short.

CRYPTO_MAP = {
    # --- Identification ---
    "symbol": "asset__symbol",       # handled indirectly via AssetIdentifier
    "name": "asset__name",
    "exchange": "exchange",

    # --- Market data ---
    "price": "last_price",
    "marketCap": "market_cap",
    "volume": "volume_24h",
    "dayHigh": "day_high",
    "dayLow": "day_low",
    "yearHigh": "year_high",
    "yearLow": "year_low",
    "open": "open_price",
    "previousClose": "previous_close",
    "change": "change",  # optional — not all CryptoDetail models have this yet
    "changePercentage": "changes_percentage",
    "priceAvg50": "price_avg_50",
    "priceAvg200": "price_avg_200",

    # --- Extended / misc ---
    "timestamp": "last_updated_ts",
}
