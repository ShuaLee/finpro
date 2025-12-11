import logging
import requests

from apps.external_data.shared.http import get_json, ExternalDataProviderUnavailable
from external_data.fmp.equities.mappings import (
    EQUITY_PROFILE_MAP,
    parse_equity_quote,
    parse_identifiers,
)
from external_data.fmp.shared.constants import (
    FMP_ACTIVELY_TRADING,
    FMP_API_KEY,
    FMP_BULK_PROFILE,
    FMP_CIK,
    FMP_CUSIP,
    FMP_DIVIDENDS,
    FMP_ISIN,
    FMP_STOCK_LIST,
    FMP_STOCK_PROFILE,
    FMP_STOCK_QUOTE_SHORT,
)
from external_data.fmp.shared.normalize import normalize_fmp_data

logger = logging.getLogger(__name__)

# --------------------------------------------------
# SINGLE PROFILE
# --------------------------------------------------


def fetch_equity_profile(symbol: str) -> dict | None:
    """
    Fetch a normalized equity profile AND the identifiers.
    Returns:
        {
            "profile": {...normalized profile data...},
            "identifiers": {...ticker/isin/cusip/cik...}
        }
    """
    url = f"{FMP_STOCK_PROFILE}?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise  # let service layer handle outage message

    if not raw or not isinstance(raw, list):
        return None

    for row in raw:
        if row.get("symbol", "").upper() != symbol.upper():
            continue

        profile = normalize_fmp_data(row, EQUITY_PROFILE_MAP)
        identifiers = parse_identifiers(row)

        return {
            "profile": profile,
            "identifiers": identifiers,
        }

    return None

# --------------------------------------------------
# BULK PROFILES (Iterates parts until FMP returns [])
# --------------------------------------------------


def _fetch_equity_profiles_bulk(part: int = 0) -> list[dict]:
    """
    Fetch a single bulk profile chunk from FMP.
    Returns a list of normalized profile dicts.
    """
    url = f"{FMP_BULK_PROFILE}?part={part}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not raw or not isinstance(raw, list):
        return []

    return [
        normalize_fmp_data(row, EQUITY_PROFILE_MAP) for row in raw if isinstance(row, dict)
    ]


def fetch_all_equity_profiles_bulk() -> list[dict]:
    """
    Fetch ALL FMP profile-bulk parts, iterating part=0,1,2,... 
    until FMP returns [].

    This may return tens of thousands of profiles.
    Suitable ONLY for:
        - initial DB seeding
        - scheduled deep metadata sync
    """
    all_profiles = []
    part = 0

    while True:
        logger.info(f"Fetching FMP profile-bulk part={part}...")
        chunk = _fetch_equity_profiles_bulk(part)

        # Stop when FMP returns no more chunks
        if not chunk:
            logger.info(f"No more bulk profile parts after part={part}. Done.")
            break

        all_profiles.extend(chunk)
        part += 1

    logger.info(f"Fetched {len(all_profiles)} total equity profiles (bulk).")
    return all_profiles


# --------------------------------------------------
# SINGLE QUOTE FETCH (Uses parse_equity_quote)
# --------------------------------------------------


def fetch_equity_quote(symbol: str) -> dict | None:
    """
    Fetch only the fast-moving quote values for a symbol.
    """
    url = f"{FMP_STOCK_QUOTE_SHORT}?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not raw or not isinstance(raw, list):
        return None

    return parse_equity_quote(raw[0])

# --------------------------------------------------
# BULK QUOTES
# --------------------------------------------------


def fetch_equity_quotes_bulk(symbols: list[str]) -> list[dict]:
    """
    Fetch quotes for many symbols at once, using the lightweight quote parser.
    """
    if not symbols:
        return []

    joined = ",".join(symbols)
    url = f"{FMP_STOCK_QUOTE_SHORT}?symbol={joined}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not raw or not isinstance(raw, list):
        return []

    return [
        parse_equity_quote(row) for row in raw if isinstance(row, dict)
    ]


# --------------------------------------------------
# EQUITY UNIVERSE
# --------------------------------------------------
def fetch_equity_list() -> list[dict]:
    """
    Return FMP's lightweight stock list:
    [
       {"symbol": "AAPL", "name": "...", "exchange": "..."},
       ...
    ]
    """
    url = f"{FMP_STOCK_LIST}?apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    return raw if isinstance(raw, list) else []


# --------------------------------------------------
# ACTIVELY TRADING LIST
# --------------------------------------------------
def fetch_actively_trading_list() -> set[str]:
    """
    Returns a set of symbols that FMP currently classifies as 'actively trading'.
    """
    url = f"{FMP_ACTIVELY_TRADING}?apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not isinstance(raw, list):
        return set()

    return {item["symbol"].upper() for item in raw if "symbol" in item}


# --------------------------------------------------
# FETCH BY IDENTIFIERS
# --------------------------------------------------
def fetch_equity_by_isin(isin: str) -> dict | None:
    """
    Fetch equity identity info using an ISIN lookup.
    NOTE: This endpoint does NOT return full profile data.
    Returns:
        {
            "symbol": ...,
            "identifiers": {...}
        }
    """
    url = f"{FMP_ISIN}?isin={isin}&apikey={FMP_API_KEY}"

    try:
        raw = get_json
    except ExternalDataProviderUnavailable:
        raise

    if not isinstance(raw, list) or not raw:
        return None
    
    row = raw[0]

    identifiers = {
        "TICKER": row.get("symbol"),
        "ISIN": row.get("isin"),
    }

    return {
        "symbol": row.get("symbol"),
        "identifiers": identifiers,
    }

def fetch_equity_profile_by_cik(cik: str) -> dict | None:
    """
    Fetch a normalized equity profile using a CIK.
    Returns:
        {
            "profile": {...normalized fields...},
            "identifiers": {...ticker/isin/cusip/cik...}
        }
    """
    url = f"{FMP_CIK}?cik={cik}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not raw or not isinstance(raw, list):
        return None

    row = raw[0]  # FMP always returns a list

    profile = normalize_fmp_data(row, EQUITY_PROFILE_MAP)
    identifiers = parse_identifiers(row)

    return {
        "profile": profile,
        "identifiers": identifiers,
    }

def fetch_equity_by_cusip(cusip: str) -> dict | None:
    """
    Fetch equity identity info using a CUSIP lookup.
    Only returns identity info, not full profile.
    """
    url = f"{FMP_CUSIP}?cusip={cusip}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise

    if not raw or not isinstance(raw, list) or not raw:
        return None

    row = raw[0]

    identifiers = {
        "TICKER": row.get("symbol"),
        "CUSIP": row.get("cusip"),
    }

    return {
        "symbol": row.get("symbol"),
        "identifiers": identifiers,
    }


# --------------------------------------------------
# FETCH DIVIDENDS
# --------------------------------------------------
def fetch_equity_dividends(symbol: str) -> list[dict] | None:
    """
    Fetch the full list of dividend events for an equity.
    Returns a list of raw dividend dictionaries OR None on failure.

    FMP returns structure:
    {
        "symbol": "AAPL",
        "historical": [
            {
                "date": "2025-11-10",
                "recordDate": "2025-11-10",
                "paymentDate": "2025-11-13",
                "declarationDate": "2025-10-30",
                "adjDividend": 0.26,
                "dividend": 0.26,
                "yield": 0.38,
                "frequency": "Quarterly"
            },
            ...
        ]
    }
    """
    url = f"{FMP_DIVIDENDS}/{symbol}?apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise  # let upper layer handle outage

    if not raw or "historical" not in raw:
        return None

    historical = raw.get("historical", [])
    if not isinstance(historical, list):
        return None

    return historical