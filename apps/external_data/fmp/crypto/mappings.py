"""
Field mappings for FMP → CryptoDetail model.
The FMP /quote endpoint contains both identity and quote data for crypto,
so we unify everything into a single map.
"""

CRYPTO_MAP = {
    # Identity
    "symbol": "asset__symbol",
    "name": "asset__name",
    "exchange": "exchange",

    # Market data
    "price": "last_price",
    "marketCap": "market_cap",
    "volume": "volume_24h",
}