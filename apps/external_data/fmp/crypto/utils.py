def split_crypto_pair(symbol: str) -> tuple[str, str]:
    """
    Split a crypto pair (BTCUSD -> ('BTC', 'USD')).
    FMP currently only uses USD pairs, but we keep this generic.

    Rules:
    - Last 3 letters = quote if alphabetic (USD, EUR, GBP, etc.)
    - Else: treat whole symbol as base
    """
    symbol = symbol.upper().strip()

    if len(symbol) > 3 and symbol[-3:].isalpha():
        return symbol[:-3], symbol[-3:]

    return symbol, None


def clean_crypto_name(name: str) -> str | None:
    if not name:
        return None
    name = name.strip()
    # FMP always appends " USD"
    if name.upper().endswith(" USD"):
        return name[:-4].strip()
    return name
