from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData, AssetType
from apps.assets.services import AssetService
from apps.integrations.exceptions import EmptyProviderResult, IntegrationError
from apps.integrations.models import ActiveEquityListing
from apps.integrations.services.held_equity_review_service import HeldEquityReviewService


class ActiveEquityAssetService:
    @staticmethod
    def _get_equity_type() -> AssetType:
        asset_type = AssetType.objects.filter(
            created_by__isnull=True,
            slug="equity",
        ).first()
        if asset_type is None:
            raise ValidationError("System asset type 'Equity' is required before tracked equities can be added.")
        return asset_type

    @staticmethod
    def _get_active_listing(*, symbol: str) -> ActiveEquityListing:
        normalized = (symbol or "").strip().upper()
        listing = ActiveEquityListing.objects.filter(provider="fmp", symbol=normalized).first()
        if listing is None:
            raise ValidationError({"active_equity_symbol": "That stock is not in the current active equity list."})
        return listing

    @staticmethod
    def _names_are_consistent(left: str, right: str) -> bool:
        return HeldEquityReviewService._names_are_consistent(left, right)

    @staticmethod
    @transaction.atomic
    def get_or_create_public_asset(*, symbol: str) -> Asset:
        listing = ActiveEquityAssetService._get_active_listing(symbol=symbol)
        equity_type = ActiveEquityAssetService._get_equity_type()

        asset = (
            Asset.objects.select_related("market_data")
            .filter(
                owner__isnull=True,
                asset_type=equity_type,
                market_data__provider=AssetMarketData.Provider.FMP,
                market_data__provider_symbol=listing.symbol,
            )
            .first()
        )

        if asset is None:
            asset = (
                Asset.objects.select_related("market_data")
                .filter(
                    owner__isnull=True,
                    asset_type=equity_type,
                    symbol=listing.symbol,
                )
                .first()
            )

        if asset is not None:
            current_name = getattr(getattr(asset, "market_data", None), "last_seen_name", "") or asset.name
            if current_name and not ActiveEquityAssetService._names_are_consistent(current_name, listing.name):
                raise ValidationError(
                    {
                        "active_equity_symbol": (
                            "This ticker already maps to a different stored asset and needs review before reuse."
                        )
                    }
                )
        else:
            try:
                asset = AssetService.create_asset(
                    asset_type=equity_type,
                    owner=None,
                    name=listing.name,
                    symbol=listing.symbol,
                    data={
                        "active_equity_listing": {
                            "provider": listing.provider,
                            "symbol": listing.symbol,
                            "name": listing.name,
                        }
                    },
                    is_active=True,
                )
            except IntegrityError as exc:
                raise ValidationError(
                    {
                        "active_equity_symbol": (
                            "A public asset with that ticker already exists and needs review before it can be reused."
                        )
                    }
                ) from exc

        market_data = getattr(asset, "market_data", None)
        if market_data is None:
            market_data = AssetMarketData(
                asset=asset,
                provider=AssetMarketData.Provider.FMP,
            )

        now = timezone.now()
        market_data.provider_symbol = listing.symbol
        market_data.last_seen_symbol = listing.symbol
        market_data.last_seen_name = listing.name
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = now
        market_data.last_successful_sync_at = now
        market_data.last_error = ""
        market_data.save()

        asset.name = listing.name
        asset.symbol = listing.symbol
        asset.is_active = True
        asset.data = {
            **asset.data,
            "active_equity_listing": {
                "provider": listing.provider,
                "symbol": listing.symbol,
                "name": listing.name,
            },
        }
        asset.save()
        return asset

    @staticmethod
    def ensure_identity_for_held_asset(*, asset: Asset) -> AssetMarketData | None:
        if asset.owner is not None:
            return None

        if asset.asset_type.slug != "equity":
            return None

        market_data = getattr(asset, "market_data", None)
        if market_data and any([market_data.isin, market_data.cusip, market_data.cik]):
            return market_data

        try:
            return HeldEquityReviewService.enrich_identity(asset=asset)
        except (EmptyProviderResult, IntegrationError) as exc:
            if market_data is None:
                market_data = AssetMarketData(
                    asset=asset,
                    provider=AssetMarketData.Provider.FMP,
                )

            market_data.provider_symbol = market_data.provider_symbol or asset.symbol
            market_data.last_seen_symbol = market_data.last_seen_symbol or asset.symbol
            market_data.last_seen_name = market_data.last_seen_name or asset.name
            market_data.status = AssetMarketData.Status.NEEDS_REVIEW
            market_data.last_synced_at = timezone.now()
            market_data.last_error = str(exc)
            market_data.save()
            return market_data
