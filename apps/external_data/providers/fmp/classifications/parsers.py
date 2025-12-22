def parse_sector(row: dict) -> str | None:
    """
    Extract sector name from FMP sector row.
    """
    return row.get("sector")


def parse_industry(row: dict) -> str | None:
    """
    Extract industry name from FMP industry row.
    """
    return row.get("industry")


def parse_exchange(row: dict) -> dict | None:
    """
    Extract exchange metadata from FMP exchange row.
    Normalization is NOT done here.
    """
    if not isinstance(row, dict):
        return None

    if "exchange" not in row or "name" not in row:
        return None

    return {
        "code": row.get("exchange"),
        "name": row.get("name"),
        "country_name": row.get("countryName"),
        "country_code": row.get("countryCode"),
        "symbol_suffix": row.get("symbolSuffix"),
        "delay": row.get("delay"),
    }
