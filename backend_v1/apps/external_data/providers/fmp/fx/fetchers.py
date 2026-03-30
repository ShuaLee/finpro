from external_data.exceptions import ExternalDataEmptyResult, ExternalDataInvalidResponse
from external_data.providers.fmp.constants import (
    AVAILABLE_COUNTRIES,
    FOREX_BATCH_QUOTES,
    FOREX_LIST,
    QUOTE_SHORT,
)
from external_data.providers.fmp.fx.parsers import parse_fx_quote
from external_data.providers.fmp.request import fmp_get_json


def fetch_fx_universe() -> list[dict]:
    data = fmp_get_json(FOREX_LIST)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid FX universe response.")
    return data


def fetch_fx_quote(symbol: str) -> dict:
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ExternalDataInvalidResponse("Symbol is required for FX quote.")

    data = fmp_get_json(QUOTE_SHORT, symbol=symbol)
    if not isinstance(data, list) or not data:
        raise ExternalDataEmptyResult(f"No FX quote for {symbol}.")

    parsed = parse_fx_quote(data[0])
    if not parsed:
        raise ExternalDataEmptyResult(f"Malformed FX quote for {symbol}.")
    return parsed


def fetch_fx_quotes_bulk(symbols: list[str], short: bool = False) -> list[dict]:
    if not symbols:
        return []

    requested = {s.upper().strip() for s in symbols if s and s.strip()}
    if not requested:
        return []

    data = fmp_get_json(FOREX_BATCH_QUOTES, short=str(short).lower())
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid FX bulk quote response.")

    results: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        symbol = (row.get("symbol") or "").upper().strip()
        if symbol not in requested:
            continue
        parsed = parse_fx_quote(row)
        if parsed:
            results.append(parsed)
    return results


def fetch_available_countries() -> list[str]:
    data = fmp_get_json(AVAILABLE_COUNTRIES)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Invalid available countries response.")

    return [
        row["country"].upper()
        for row in data
        if isinstance(row, dict) and row.get("country")
    ]
