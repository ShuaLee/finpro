from django.db import models

from apps.integrations.exceptions import EmptyProviderResult
from apps.integrations.models import ActiveCommodityListing, ActiveCryptoListing
from apps.integrations.providers.fmp import FMP_PROVIDER
from apps.integrations.services.active_equity_sync_service import ActiveEquitySyncService
from apps.integrations.services.constants import PRECIOUS_METAL_COMMODITY_MAP


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
    def get_forex_list():
        return FMP_PROVIDER.get_forex_list()

    @staticmethod
    def get_available_countries():
        return FMP_PROVIDER.get_available_countries()

    @staticmethod
    def search_active_equities(*, query: str):
        queryset = ActiveEquitySyncService.get_queryset(provider="fmp")
        normalized = (query or "").strip()
        if normalized:
            queryset = queryset.filter(
                models.Q(symbol__icontains=normalized) | models.Q(name__icontains=normalized)
            )
        return queryset.order_by("symbol")

    @staticmethod
    def search_active_cryptos(*, query: str):
        queryset = ActiveCryptoListing.objects.filter(provider="fmp")
        normalized = (query or "").strip()
        if normalized:
            queryset = queryset.filter(
                models.Q(symbol__icontains=normalized)
                | models.Q(name__icontains=normalized)
                | models.Q(base_symbol__icontains=normalized)
            )
        return queryset.order_by("symbol")

    @staticmethod
    def search_active_commodities(*, query: str):
        queryset = ActiveCommodityListing.objects.filter(provider="fmp")
        normalized = (query or "").strip()
        if normalized:
            queryset = queryset.filter(
                models.Q(symbol__icontains=normalized) | models.Q(name__icontains=normalized)
            )
        return queryset.order_by("symbol")

    @staticmethod
    def get_active_precious_metals() -> list[dict]:
        commodity_listings = {
            listing.symbol: listing
            for listing in ActiveCommodityListing.objects.filter(
                provider="fmp",
                symbol__in=[spec["symbol"] for spec in PRECIOUS_METAL_COMMODITY_MAP.values()],
            )
        }

        rows: list[dict] = []
        for metal, spec in PRECIOUS_METAL_COMMODITY_MAP.items():
            commodity = commodity_listings.get(spec["symbol"])
            if commodity is None:
                continue
            rows.append(
                {
                    "metal": metal,
                    "name": spec["name"],
                    "spot_symbol": commodity.symbol,
                    "spot_name": commodity.name,
                    "currency": commodity.currency,
                }
            )
        return rows

    @staticmethod
    def get_profile_with_identifiers(*, symbol: str):
        return FMP_PROVIDER.get_profile_with_identifiers(symbol)

    @staticmethod
    def get_quote_for_asset(*, asset):
        symbol = (getattr(asset, "symbol", "") or "").strip().upper()
        if not symbol:
            raise EmptyProviderResult("Asset has no symbol for market data lookup.")
        return FMP_PROVIDER.get_quote(symbol)
