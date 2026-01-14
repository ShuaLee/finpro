from datetime import date, datetime
from decimal import Decimal, InvalidOperation


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _dec(val):
    try:
        return Decimal(str(val)) if val is not None else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_date(val):
    if not val:
        return None
    if hasattr(val, "year"):
        return val
    return datetime.strptime(val, "%Y-%m-%d").date()


# --------------------------------------------------
# Parsers
# --------------------------------------------------

def parse_identifiers(raw: dict) -> dict:
    return {
        "TICKER": raw.get("symbol"),
        "ISIN": raw.get("isin"),
        "CUSIP": raw.get("cusip"),
        "CIK": raw.get("cik"),
    }


def parse_equity_quote(raw: dict) -> dict:
    return {
        "price": _dec(raw.get("price")),
        "change": _dec(raw.get("change")),
        "volume": raw.get("volume"),
    }


def parse_dividend_event(raw: dict) -> dict | None:
    """
    Normalize FMP dividend event.
    """
    # Choose best available date (priority order)
    date_str = (
        raw.get("paymentDate")
        or raw.get("recordDate")
        or raw.get("declarationDate")
    )

    if not date_str:
        return None

    try:
        event_date = date.fromisoformat(date_str)
    except ValueError:
        return None

    dividend = raw.get("dividend")
    if dividend is None:
        return None

    return {
        "date": event_date,
        "dividend": Decimal(str(dividend)),
        "frequency": raw.get("frequency"),
    }


# --------------------------------------------------
# Profile normalization map
# --------------------------------------------------

EQUITY_PROFILE_MAP = {
    "companyName": "name",
    "website": "website",
    "description": "description",
    "image": "image_url",

    "sector": "sector",
    "industry": "industry",
    "exchange": "exchange",
    "country": "country",

    "marketCap": "market_cap",
    "beta": "beta",
    "lastDividend": "last_dividend",
    "ipoDate": "ipo_date",

    "isEtf": "is_etf",
    "isAdr": "is_adr",
    "isFund": "is_fund",
    "isActivelyTrading": "is_actively_trading",

    "currency": "currency",
}
