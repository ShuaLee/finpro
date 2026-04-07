from django.db import models

from apps.integrations.exceptions import EmptyProviderResult
from apps.integrations.providers.fmp import FMP_PROVIDER
from apps.integrations.services.equity_directory_sync_service import EquityDirectorySyncService


class MarketDataService:
    @staticmethod
    def get_quote_for_symbol(*, symbol: str):
        return FMP_PROVIDER.get_quote(symbol)

    @staticmethod
    def get_profile_for_symbol(*, symbol: str):
        return FMP_PROVIDER.get_company_profile(symbol)

    @staticmethod
    def get_stock_list():
        return FMP_PROVIDER.get_stock_list()

    @staticmethod
    def get_actively_traded_symbols():
        return FMP_PROVIDER.get_actively_traded_symbols()

    @staticmethod
    def search_active_equities(*, query: str):
        queryset = EquityDirectorySyncService.get_active_entries(provider="fmp").filter(
            is_actively_traded=True
        )
        normalized = (query or "").strip()
        if normalized:
            queryset = queryset.filter(
                models.Q(symbol__icontains=normalized) | models.Q(name__icontains=normalized)
            )
        return queryset.order_by("symbol")

    @staticmethod
    def get_quote_for_asset(*, asset):
        symbol = (getattr(asset, "symbol", "") or "").strip().upper()
        if not symbol:
            raise EmptyProviderResult("Asset has no symbol for market data lookup.")
        return FMP_PROVIDER.get_quote(symbol)
