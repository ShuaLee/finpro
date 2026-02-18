from decimal import Decimal, InvalidOperation


def _dec(val):
    try:
        return Decimal(str(val)) if val is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def normalize_currency(code: str | None) -> str:
    """
    FMP sometimes emits USX for commodity quotes; normalize to USD.
    """
    if not code:
        return "USD"
    code = code.upper().strip()
    if code == "USX":
        return "USD"
    return code


def parse_commodity_list_row(raw: dict) -> dict:
    symbol = raw.get("symbol")
    if not symbol:
        return {}

    return {
        "symbol": symbol,
        "name": raw.get("name"),
        "exchange": raw.get("exchange"),
        "trade_month": raw.get("tradeMonth"),
        "currency_code": normalize_currency(raw.get("currency")),
    }


def parse_commodity_quote_short(raw: dict) -> dict:
    return {
        "price": _dec(raw.get("price")),
        "change": _dec(raw.get("change")),
        "volume": _dec(raw.get("volume")),
    }
