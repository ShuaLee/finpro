from external_data.shared.http import get_json
from external_data.exceptions import ExternalDataEmptyResult, ExternalDataProviderUnavailable

from external_data.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_API_KEY,
    FOREX_LIST,
    QUOTE_SHORT,
    FOREX_BATCH_QUOTES,
    AVAILABLE_COUNTRIES,
)

from .parsers import parse_fx_quote


# --------------------------------------------------
# FX Universe
# --------------------------------------------------

def fetch_fx_universe() -> list[dict]:
    """
    Fetch the complete list of forex pairs from FMP.
    """
    api_key = _api_key_or_raise()
    url = f"{FMP_BASE_URL}{FOREX_LIST}?apikey={api_key}"
    data = get_json(url)

    if not isinstance(data, list):
        raise ExternalDataEmptyResult("Invalid FX universe response")

    return data


# --------------------------------------------------
# Single FX quote
# --------------------------------------------------

def fetch_fx_quote(symbol: str) -> dict:
    """
    Fetch a single FX quote using a fully-qualified symbol (e.g. 'EURUSD').
    """
    api_key = _api_key_or_raise()
    url = f"{FMP_BASE_URL}{QUOTE_SHORT}?symbol={symbol}&apikey={api_key}"
    data = get_json(url)

    if not data:
        raise ExternalDataEmptyResult(f"No FX quote for {symbol}")

    parsed = parse_fx_quote(data[0])
    if not parsed:
        raise ExternalDataEmptyResult(f"Malformed FX quote for {symbol}")

    return parsed


# --------------------------------------------------
# Bulk FX quotes
# --------------------------------------------------

def fetch_fx_quotes_bulk(symbols: list[str], short: bool = False) -> list[dict]:
    """
    Fetch FX quotes for multiple symbols.
    """
    if not symbols:
        return []

    api_key = _api_key_or_raise()
    url = f"{FMP_BASE_URL}{FOREX_BATCH_QUOTES}?apikey={api_key}"
    if short:
        url += "&short=true"

    data = get_json(url)

    results = []
    for row in data:
        parsed = parse_fx_quote(row)
        if parsed:
            results.append(parsed)

    return results


# --------------------------------------------------
# Available countries
# --------------------------------------------------

def fetch_available_countries() -> list[str]:
    api_key = _api_key_or_raise()
    url = f"{FMP_BASE_URL}{AVAILABLE_COUNTRIES}?apikey={api_key}"
    data = get_json(url)

    if not isinstance(data, list):
        raise ExternalDataEmptyResult("Invalid available countries response")

    return [
        row["country"].upper()
        for row in data
        if isinstance(row, dict) and row.get("country")
    ]
def _api_key_or_raise() -> str:
    if not FMP_API_KEY:
        raise ExternalDataProviderUnavailable("FMP_API_KEY is not configured.")
    return FMP_API_KEY
