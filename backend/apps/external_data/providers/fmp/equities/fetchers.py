from external_data.exceptions import ExternalDataEmptyResult, ExternalDataInvalidResponse
from external_data.providers.fmp.constants import (
    ACTIVELY_TRADING_LIST,
    DIVIDENDS,
    PROFILE,
    QUOTE_SHORT,
)
from external_data.providers.fmp.equities.parsers import (
    EQUITY_PROFILE_MAP,
    parse_dividend_event,
    parse_equity_quote,
    parse_identifiers,
)
from external_data.providers.fmp.request import fmp_get_json
from external_data.shared.normalize import normalize_fmp_data


def fetch_equity_profile(symbol: str) -> dict:
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ExternalDataInvalidResponse("Symbol is required for equity profile.")

    data = fmp_get_json(PROFILE, symbol=symbol)

    if not isinstance(data, list) or not data:
        raise ExternalDataEmptyResult(f"No profile for symbol {symbol}.")

    row = data[0]
    if not isinstance(row, dict):
        raise ExternalDataInvalidResponse(f"Malformed profile payload for {symbol}.")

    return {
        "profile": normalize_fmp_data(row, EQUITY_PROFILE_MAP),
        "identifiers": parse_identifiers(row),
    }


def fetch_equity_quote_short(symbol: str) -> dict:
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ExternalDataInvalidResponse("Symbol is required for equity quote.")

    data = fmp_get_json(QUOTE_SHORT, symbol=symbol)
    if not isinstance(data, list) or not data:
        raise ExternalDataEmptyResult(f"No quote for symbol {symbol}.")

    row = data[0]
    if not isinstance(row, dict):
        raise ExternalDataInvalidResponse(f"Malformed quote payload for {symbol}.")

    return parse_equity_quote(row)


def fetch_equity_dividends(symbol: str) -> list[dict]:
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise ExternalDataInvalidResponse("Symbol is required for equity dividends.")

    data = fmp_get_json(DIVIDENDS, symbol=symbol)
    if not isinstance(data, list):
        return []

    events: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        parsed = parse_dividend_event(row)
        if parsed:
            events.append(parsed)

    return events


def fetch_actively_trading_equity_symbols() -> set[str]:
    data = fmp_get_json(ACTIVELY_TRADING_LIST)
    if not isinstance(data, list):
        raise ExternalDataInvalidResponse("Malformed actively trading list payload.")

    symbols = {
        (row.get("symbol") or "").upper().strip()
        for row in data
        if isinstance(row, dict)
    }
    symbols.discard("")
    return symbols
