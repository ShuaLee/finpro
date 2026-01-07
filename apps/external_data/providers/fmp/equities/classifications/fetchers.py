from external_data.shared.http import get_json
from external_data.exceptions import ExternalDataEmptyResult

from external_data.providers.fmp.constants import (
    FMP_BASE_URL,
    FMP_API_KEY,
    AVAILABLE_SECTORS,
    AVAILABLE_INDUSTRIES,
    AVAILABLE_EXCHANGES,
)

from .parsers import (
    parse_sector,
    parse_industry,
    parse_exchange,
)


# --------------------------------------------------
# Sectors
# --------------------------------------------------

def fetch_available_sectors() -> list[str]:
    url = f"{FMP_BASE_URL}{AVAILABLE_SECTORS}?apikey={FMP_API_KEY}"
    data = get_json(url)

    if not isinstance(data, list):
        raise ExternalDataEmptyResult("Invalid available-sectors response")

    return [
        sector
        for row in data
        if (sector := parse_sector(row))
    ]


# --------------------------------------------------
# Industries
# --------------------------------------------------

def fetch_available_industries() -> list[str]:
    url = f"{FMP_BASE_URL}{AVAILABLE_INDUSTRIES}?apikey={FMP_API_KEY}"
    data = get_json(url)

    if not isinstance(data, list):
        raise ExternalDataEmptyResult("Invalid available-industries response")

    return [
        industry
        for row in data
        if (industry := parse_industry(row))
    ]


# --------------------------------------------------
# Exchanges
# --------------------------------------------------

def fetch_available_exchanges() -> list[dict]:
    """
    Fetch exchange metadata from FMP.

    Normalization / DB mapping happens in the service or seeder layer.
    """
    url = f"{FMP_BASE_URL}{AVAILABLE_EXCHANGES}?apikey={FMP_API_KEY}"
    data = get_json(url)

    if not isinstance(data, list):
        raise ExternalDataEmptyResult("Invalid available-exchanges response")

    exchanges = []
    for row in data:
        parsed = parse_exchange(row)
        if parsed:
            exchanges.append(parsed)

    return exchanges
