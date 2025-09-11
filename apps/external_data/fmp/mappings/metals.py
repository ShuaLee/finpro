from external_data.fmp.normalize import _to_decimal, _to_str, _to_int

METAL_QUOTE_MAP = {
    "last_price": ("price", _to_decimal),
    "currency": ("currency", _to_str),
    "open_price": ("open", _to_decimal),
    "day_high": ("dayHigh", _to_decimal),
    "day_low": ("dayLow", _to_decimal),
    "previous_close": ("previousClose", _to_decimal),
    "volume": ("volume", _to_int),
}
