def split_crypto_pair(symbol: str) -> tuple[str, str | None]:
    """
    Split only symbols ending in 'USD'.
    Everything else is a standalone crypto symbol.
    """
    symbol = symbol.upper().strip()

    if symbol.endswith("USD") and len(symbol) > 3:
        return symbol[:-3], "USD"

    # Standalone token, no separate quote currency
    return symbol, None


def clean_crypto_name(name: str) -> str | None:
    if not name:
        return None
    name = name.strip()
    # FMP always appends " USD"
    if name.upper().endswith(" USD"):
        return name[:-4].strip()
    return name
