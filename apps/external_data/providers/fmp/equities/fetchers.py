from external_data.exceptions import (
    ExternalDataEmptyResult,
)
from external_data.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_API_KEY,
    PROFILE,
    QUOTE_SHORT,
    SEARCH_ISIN,
    SEARCH_CUSIP,
    SEARCH_CIK,
    DIVIDENDS,
    STOCK_LIST,
    ACTIVELY_TRADING_LIST,
)
from external_data.shared.http import get_json
from external_data.shared.normalize import normalize_fmp_data
from external_data.providers.fmp.equities.parsers import (
    EQUITY_PROFILE_MAP,
    parse_identifiers,
    parse_equity_quote,
    parse_dividend_event,
)


# --------------------------------------------------
# Profile / identity
# --------------------------------------------------

def fetch_equity_profile(symbol: str) -> dict:
    url = f"{FMP_BASE_URL}{PROFILE}?symbol={symbol}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No profile for symbol {symbol}")

    row = data[0]

    return {
        "profile": normalize_fmp_data(row, EQUITY_PROFILE_MAP),
        "identifiers": parse_identifiers(row),
    }

# --------------------------------------------------
# Identifiers
# --------------------------------------------------


def fetch_equity_by_isin(isin: str) -> dict:
    url = f"{FMP_BASE_URL}{SEARCH_ISIN}?isin={isin}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No equity found for ISIN {isin}")

    row = data[0]

    return {
        "symbol": row.get("symbol"),
        "identifiers": parse_identifiers(row),
    }


def fetch_equity_by_cusip(cusip: str) -> dict:
    url = f"{FMP_BASE_URL}{SEARCH_CUSIP}?cusip={cusip}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No equity found for CUSIP {cusip}")

    row = data[0]

    return {
        "symbol": row.get("symbol"),
        "identifiers": parse_identifiers(row),
    }


def fetch_equity_by_cik(cik: str) -> dict:
    url = f"{FMP_BASE_URL}{SEARCH_CIK}?cik={cik}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No equity found for CIK {cik}")

    row = data[0]

    return {
        "symbol": row.get("symbol"),
        "identifiers": parse_identifiers(row),
    }

# --------------------------------------------------
# Quotes
# --------------------------------------------------


def fetch_equity_quote_short(symbol: str) -> dict:
    url = f"{FMP_BASE_URL}{QUOTE_SHORT}?symbol={symbol}&apikey={FMP_API_KEY}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No quote for symbol {symbol}")

    return parse_equity_quote(data[0])

# --------------------------------------------------
# Dividends
# --------------------------------------------------


def fetch_equity_dividends(symbol: str) -> list[dict]:
    url = f"{FMP_BASE_URL}{DIVIDENDS}?symbol={symbol}&apikey={FMP_API_KEY}"
    data = get_json(url)

    # Empty list is VALID here
    return [parse_dividend_event(row) for row in data] if data else []


# --------------------------------------------------
# Universes
# --------------------------------------------------

def fetch_equity_list() -> list[dict]:
    url = f"{FMP_BASE_URL}{STOCK_LIST}?apikey={FMP_API_KEY}"
    return get_json(url)


def fetch_actively_trading_symbols() -> set[str]:
    url = f"{FMP_BASE_URL}{ACTIVELY_TRADING_LIST}?apikey={FMP_API_KEY}"
    data = get_json(url)
    return {row["symbol"].upper() for row in data if "symbol" in row}
