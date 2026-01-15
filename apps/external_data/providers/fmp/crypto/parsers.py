from decimal import Decimal, InvalidOperation
from typing import NamedTuple


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _dec(val):
    try:
        return Decimal(str(val)) if val is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return None


class CryptoPair(NamedTuple):
    base_symbol: str
    quote_currency: str


# Order matters (longest first)
KNOWN_QUOTES = (
    "USDT",
    "USDC",
    "USD",
    "EUR",
    "GBP",
)


def split_crypto_pair(pair_symbol: str) -> CryptoPair:
    """
    Split a crypto pair symbol into base + quote currency.

    Examples:
        BTCUSD  -> (BTC, USD)
        ETHUSDT -> (ETH, USDT)
        ETHEUR  -> (ETH, EUR)
    """
    if not pair_symbol:
        raise ValueError("Empty crypto pair symbol")

    pair = pair_symbol.upper().strip()

    for quote in KNOWN_QUOTES:
        if pair.endswith(quote) and len(pair) > len(quote):
            return CryptoPair(
                base_symbol=pair[:-len(quote)],
                quote_currency=quote,
            )

    raise ValueError(f"Unrecognized crypto pair symbol: {pair_symbol}")


# -------------------------------------------------
# Parsers
# -------------------------------------------------

def parse_crypto_list_row(raw: dict) -> dict:
    pair_symbol = raw.get("symbol")
    if not pair_symbol:
        return {}

    try:
        base_symbol, quote_currency = split_crypto_pair(pair_symbol)
    except ValueError:
        return {}

    return {
        "pair_symbol": pair_symbol,
        "base_symbol": base_symbol,
        "currency_code": quote_currency,
        "name": raw.get("name"),
        "ico_date": raw.get("icoDate"),
        "circulating_supply": _dec(raw.get("circulatingSupply")),
        "total_supply": _dec(raw.get("totalSupply")),
    }


def parse_crypto_quote_short(raw: dict) -> dict:
    return {
        "price": _dec(raw.get("price")),
        "change": _dec(raw.get("change")),
        "volume": _dec(raw.get("volume")),
    }
