from apps.integrations.exceptions import EmptyProviderResult, InvalidProviderResponse
from apps.integrations.providers.fmp.constants import (
    ACTIVELY_TRADING_LIST,
    DIVIDENDS,
    PROFILE,
    PROVIDER_NAME,
    QUOTE_SHORT,
    STOCK_LIST,
)
from apps.integrations.providers.fmp.parsers import (
    parse_actively_traded_row,
    parse_company_profile_payload,
    parse_quote_payload,
    parse_stock_list_row,
)
from apps.integrations.providers.fmp.request import fmp_get_json
from apps.integrations.providers.market_data import MarketDataProvider
from apps.integrations.shared.types import CompanyProfile, QuoteSnapshot


class FMPProvider(MarketDataProvider):
    name = PROVIDER_NAME

    def get_quote(self, symbol: str) -> QuoteSnapshot:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for quote lookup.")

        data = fmp_get_json(QUOTE_SHORT, symbol=normalized)
        if not isinstance(data, list) or not data:
            raise EmptyProviderResult(f"No quote found for {normalized}.")
        row = data[0]
        if not isinstance(row, dict):
            raise InvalidProviderResponse(f"Malformed quote payload for {normalized}.")
        return parse_quote_payload(row, source=self.name)

    def get_company_profile(self, symbol: str) -> CompanyProfile:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for profile lookup.")

        data = fmp_get_json(PROFILE, symbol=normalized)
        if not isinstance(data, list) or not data:
            raise EmptyProviderResult(f"No profile found for {normalized}.")
        row = data[0]
        if not isinstance(row, dict):
            raise InvalidProviderResponse(f"Malformed profile payload for {normalized}.")
        return parse_company_profile_payload(row)

    def get_dividends(self, symbol: str) -> list[dict]:
        normalized = (symbol or "").strip().upper()
        if not normalized:
            raise InvalidProviderResponse("Symbol is required for dividend lookup.")

        data = fmp_get_json(DIVIDENDS, symbol=normalized)
        if not isinstance(data, list):
            return []
        return [row for row in data if isinstance(row, dict)]

    def get_stock_list(self) -> list[dict]:
        data = fmp_get_json(STOCK_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed stock list payload.")

        parsed: list[dict] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.append(parse_stock_list_row(row))
            except InvalidProviderResponse:
                continue
        return parsed

    def get_actively_traded_symbols(self) -> set[str]:
        data = fmp_get_json(ACTIVELY_TRADING_LIST)
        if not isinstance(data, list):
            raise InvalidProviderResponse("Malformed actively trading list payload.")

        parsed: set[str] = set()
        for row in data:
            if not isinstance(row, dict):
                continue
            try:
                parsed.add(parse_actively_traded_row(row))
            except InvalidProviderResponse:
                continue
        return parsed
