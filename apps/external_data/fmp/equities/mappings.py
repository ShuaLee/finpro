def parse_equity_quote(raw: dict) -> dict:
    """
    Extract only fast-changing price fields from FMP quote endpoint.
    """
    if not raw:
        return {}

    return {
        "price": raw.get("price"),
        "change": raw.get("change"),
        "volume": raw.get("volume"),
    }


def parse_identifiers(raw: dict) -> dict:
    """
    Extract identifier fields from a profile record.
    Returned dict:
    {
        "TICKER": "...",
        "ISIN": "...",
        "CUSIP": "...",
        "CIK": "..."
    }
    """
    return {
        "TICKER": raw.get("symbol"),
        "ISIN": raw.get("isin"),
        "CUSIP": raw.get("cusip"),
        "CIK": raw.get("cik"),
    }


EQUITY_PROFILE_MAP = {
    # PROFILE FIELDS
    "companyName": "name",
    "website": "website",
    "description": "description",
    "image": "image_url",

    # RELATIONSHIPS
    "sector": "sector",
    "industry": "industry",
    "exchange": "exchange",
    "country": "country",

    # FUNDAMENTALS / SLOW DATA
    "marketCap": "market_cap",
    "beta": "beta",
    "lastDividend": "last_dividend",
    "ipoDate": "ipo_date",

    # FLAGS
    "isEtf": "is_etf",
    "isAdr": "is_adr",
    "isFund": "is_fund",
    "isActivelyTrading": "is_actively_trading",
}
