# Mapping for FMP metals → MetalDetail fields

METAL_QUOTE_MAP = {
    "price": "last_price",
    "open": "open_price",
    "dayHigh": "high_price",
    "dayLow": "low_price",
    "previousClose": "previous_close",
    "volume": "volume",
    "timestamp": "timestamp",  # optional, store raw sync time if you like
    "symbol": "symbol",        # useful if needed for debug
}
