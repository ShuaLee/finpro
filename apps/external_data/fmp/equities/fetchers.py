import logging
import requests

from apps.external_data.shared.http import get_json, ExternalDataProviderUnavailable
from external_data.fmp.equities.mappings import (
    EQUITY_PROFILE_MAP,
    parse_equity_quote
)
from external_data.fmp.shared.constants import (
    FMP_API_KEY,
    FMP_STOCK_PROFILE,
    FMP_STOCK_QUOTE,
    FMP_BULK_PROFILE,
    FMP_STOCK_LIST,
)
from external_data.fmp.shared.normalize import normalize_fmp_data

logger = logging.getLogger(__name__)

# --------------------------------------------------
# SINGLE PROFILE
# --------------------------------------------------


def fetch_equity_profile(symbol: str) -> dict | None:
    """
    Fetches a normalized equity profile for a symbol.
    Returns None on failure or no data.
    """
    url = f"{FMP_STOCK_PROFILE}?symbol={symbol}&apikey={FMP_API_KEY}"

    try:
        raw = get_json(url)
    except ExternalDataProviderUnavailable:
        raise  # let service layer handle outage message

    if not raw or not isinstance(raw, list):
        return None

    for row in raw:
        if row.get("symbol", "").upper() == symbol.upper():
            return normalize_fmp_data(row, EQUITY_PROFILE_MAP)

    return None

# --------------------------------------------------
# BULK PROFILES (Iterates parts until FMP returns [])
# --------------------------------------------------


def fetch_equity_profiles_bulk(part: int = 0) -> list[dict]:
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
        chunk = fetch_equity_profiles_bulk(part)

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
    url = f"{FMP_STOCK_QUOTE}?symbol={symbol}&apikey={FMP_API_KEY}"

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
    url = f"{FMP_STOCK_QUOTE}?symbol={joined}&apikey={FMP_API_KEY}"

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
