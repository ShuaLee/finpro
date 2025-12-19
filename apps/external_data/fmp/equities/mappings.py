from datetime import datetime
from decimal import Decimal, InvalidOperation


def parse_equity_quote(raw: dict) -> dict:
    """
    Extract fast-changing quote fields from FMP quote endpoint.
    """
    if not raw:
        return {}

    def dec(val):
        try:
            return Decimal(str(val)) if val is not None else None
        except (InvalidOperation, ValueError, TypeError):
            return None

    return {
        "price": dec(raw.get("price")),
        "change": dec(raw.get("change")),
        "volume": raw.get("volume"),  # volume is integer
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


def _parse_date(val):
    if not val:
        return None
    if hasattr(val, "year"):
        return val
    return datetime.strptime(val, "%Y-%m-%d").date()


def parse_dividend_event(raw: dict) -> dict:
    """
    Convert an FMP dividend record into fields matching EquityDividendEvent.
    Ensures date normalization for idempotent sync.
    """
    return {
        # Dates
        "ex_date": _parse_date(raw.get("date")),
        "record_date": _parse_date(raw.get("recordDate")),
        "payment_date": _parse_date(raw.get("paymentDate")),
        "declaration_date": _parse_date(raw.get("declarationDate")),

        # Amounts
        "dividend": (
            Decimal(str(raw["dividend"]))
            if raw.get("dividend") is not None
            else None
        ),
        "adj_dividend": (
            Decimal(str(raw["adjDividend"]))
            if raw.get("adjDividend") is not None
            else None
        ),

        # Metadata
        "yield_value": raw.get("yield"),
        "frequency": raw.get("frequency"),
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

    # ASSET
    "currency": "currency",
}
