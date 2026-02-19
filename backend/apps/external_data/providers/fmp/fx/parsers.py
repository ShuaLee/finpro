from decimal import Decimal, InvalidOperation


def _dec(val):
    try:
        return Decimal(str(val)) if val is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def parse_fx_symbol(symbol: str) -> tuple[str, str] | None:
    """
    Split an FX symbol like 'EURUSD' into ('EUR', 'USD').

    Returns None if malformed.
    """
    if not symbol or len(symbol) % 2 != 0:
        return None

    mid = len(symbol) // 2
    return symbol[:mid].upper(), symbol[mid:].upper()


def parse_fx_quote(raw: dict) -> dict | None:
    symbol = raw.get("symbol")
    price = raw.get("price")

    if not symbol or price is None:
        return None

    pair = parse_fx_symbol(symbol)
    if not pair:
        return None

    base, quote = pair

    return {
        "from": base,
        "to": quote,
        "rate": _dec(price),
    }
