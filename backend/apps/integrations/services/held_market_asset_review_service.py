from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData
from apps.integrations.models import ActiveCommodityListing, ActiveCryptoListing
from apps.integrations.services.constants import PRECIOUS_METAL_COMMODITY_MAP


class HeldMarketAssetReviewService:
    @staticmethod
    def _mark_tracked(*, asset: Asset, market_data: AssetMarketData, symbol: str, name: str) -> str:
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_seen_symbol = symbol
        market_data.last_seen_name = name
        market_data.last_synced_at = timezone.now()
        market_data.last_successful_sync_at = market_data.last_synced_at
        market_data.last_error = ""
        market_data.save()
        if not asset.is_active:
            asset.is_active = True
            asset.save(update_fields=["is_active", "updated_at"])
        return "tracked"

    @staticmethod
    def _mark_stale(*, asset: Asset, market_data: AssetMarketData, reason: str) -> str:
        market_data.status = AssetMarketData.Status.STALE
        market_data.last_synced_at = timezone.now()
        market_data.last_error = reason
        market_data.save()
        if asset.is_active:
            asset.is_active = False
            asset.save(update_fields=["is_active", "updated_at"])
        return "stale"

    @staticmethod
    def review_asset(*, asset: Asset) -> str:
        market_data = getattr(asset, "market_data", None)
        if market_data is None or not market_data.provider_symbol:
            return "skipped"

        slug = asset.asset_type.slug
        symbol = market_data.provider_symbol

        if slug in {"crypto", "cryptocurrency"}:
            listing = ActiveCryptoListing.objects.filter(provider="fmp", symbol=symbol).first()
            if listing is None:
                return HeldMarketAssetReviewService._mark_stale(
                    asset=asset,
                    market_data=market_data,
                    reason="Crypto pair is no longer in the current FMP crypto list.",
                )
            return HeldMarketAssetReviewService._mark_tracked(
                asset=asset,
                market_data=market_data,
                symbol=listing.symbol,
                name=listing.name,
            )

        if slug == "commodity":
            listing = ActiveCommodityListing.objects.filter(provider="fmp", symbol=symbol).first()
            if listing is None:
                return HeldMarketAssetReviewService._mark_stale(
                    asset=asset,
                    market_data=market_data,
                    reason="Commodity is no longer in the current FMP commodities list.",
                )
            return HeldMarketAssetReviewService._mark_tracked(
                asset=asset,
                market_data=market_data,
                symbol=listing.symbol,
                name=listing.name,
            )

        if slug == "precious_metal":
            metal = ((asset.data or {}).get("precious_metal_profile") or {}).get("metal", "")
            metal_spec = PRECIOUS_METAL_COMMODITY_MAP.get(metal)
            if metal_spec is None:
                return HeldMarketAssetReviewService._mark_stale(
                    asset=asset,
                    market_data=market_data,
                    reason="Precious metal mapping is missing.",
                )
            listing = ActiveCommodityListing.objects.filter(
                provider="fmp",
                symbol=metal_spec["symbol"],
            ).first()
            if listing is None:
                return HeldMarketAssetReviewService._mark_stale(
                    asset=asset,
                    market_data=market_data,
                    reason="Underlying spot commodity is no longer in the current FMP commodities list.",
                )
            return HeldMarketAssetReviewService._mark_tracked(
                asset=asset,
                market_data=market_data,
                symbol=listing.symbol,
                name=metal_spec["name"],
            )

        return "skipped"

    @staticmethod
    def review_all_tracked_assets() -> dict:
        queryset = Asset.objects.filter(
            owner__isnull=True,
            asset_type__slug__in=["crypto", "cryptocurrency", "commodity", "precious_metal"],
            market_data__provider=AssetMarketData.Provider.FMP,
        ).select_related("market_data", "asset_type")

        summary = {"tracked": 0, "stale": 0, "skipped": 0}
        for asset in queryset:
            result = HeldMarketAssetReviewService.review_asset(asset=asset)
            summary[result] = summary.get(result, 0) + 1
        return summary
