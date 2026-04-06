from typing import Iterable

from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData, AssetPrice, AssetType
from apps.integrations.exceptions import (
    EmptyProviderResult,
    IntegrationError,
)
from apps.integrations.providers.fmp import FMP_PROVIDER


class PublicAssetSyncService:
    @staticmethod
    def _resolve_asset_type(*, asset_type_slug: str) -> AssetType:
        return AssetType.objects.get(created_by__isnull=True, slug=asset_type_slug)

    @staticmethod
    def _base_asset_data_from_profile(profile) -> dict:
        return {
            "market_profile": {
                "currency": profile.currency,
                "exchange": profile.exchange,
                "sector": profile.sector,
                "industry": profile.industry,
                "country": profile.country,
                "website": profile.website,
                "image_url": profile.image_url,
            }
        }

    @staticmethod
    @transaction.atomic
    def sync_symbol(*, symbol: str, asset_type_slug: str = "equity") -> Asset:
        normalized_symbol = (symbol or "").strip().upper()
        asset_type = PublicAssetSyncService._resolve_asset_type(asset_type_slug=asset_type_slug)
        profile = FMP_PROVIDER.get_company_profile(normalized_symbol)

        defaults = {
            "name": (profile.name or normalized_symbol).strip(),
            "description": (profile.description or "").strip(),
            "is_active": True,
            "data": PublicAssetSyncService._base_asset_data_from_profile(profile),
        }

        asset, created = Asset.objects.get_or_create(
            asset_type=asset_type,
            owner=None,
            symbol=normalized_symbol,
            defaults=defaults,
        )

        if not created:
            asset.name = defaults["name"]
            asset.description = defaults["description"]
            asset.data = {**asset.data, **defaults["data"]}
            asset.is_active = True
            asset.save()

        market_data, _ = AssetMarketData.objects.get_or_create(
            asset=asset,
            defaults={
                "provider": AssetMarketData.Provider.FMP,
                "provider_symbol": normalized_symbol,
            },
        )
        market_data.provider = AssetMarketData.Provider.FMP
        market_data.provider_symbol = normalized_symbol
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = timezone.now()
        market_data.last_successful_sync_at = market_data.last_synced_at
        market_data.last_error = ""
        market_data.save()

        return asset

    @staticmethod
    @transaction.atomic
    def refresh_quote(*, asset: Asset) -> AssetPrice:
        market_data = getattr(asset, "market_data", None)
        provider_symbol = (
            getattr(market_data, "provider_symbol", "") or asset.symbol or ""
        ).strip().upper()

        quote = FMP_PROVIDER.get_quote(provider_symbol)

        price, _ = AssetPrice.objects.update_or_create(
            asset=asset,
            defaults={
                "price": quote.price,
                "change": quote.change,
                "volume": quote.volume,
                "source": quote.source or "FMP",
            },
        )

        if market_data is None:
            market_data = AssetMarketData(asset=asset, provider=AssetMarketData.Provider.FMP)

        market_data.provider_symbol = provider_symbol
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = timezone.now()
        market_data.last_successful_sync_at = market_data.last_synced_at
        market_data.last_error = ""
        market_data.save()

        asset.is_active = True
        asset.save(update_fields=["is_active", "updated_at"])

        return price

    @staticmethod
    @transaction.atomic
    def mark_asset_unresolved(*, asset: Asset, error_message: str) -> Asset:
        market_data, _ = AssetMarketData.objects.get_or_create(
            asset=asset,
            defaults={"provider": AssetMarketData.Provider.FMP},
        )
        market_data.status = AssetMarketData.Status.UNRESOLVED
        market_data.last_synced_at = timezone.now()
        market_data.last_error = error_message
        market_data.save()
        return asset

    @staticmethod
    @transaction.atomic
    def mark_asset_stale(*, asset: Asset, error_message: str) -> Asset:
        market_data, _ = AssetMarketData.objects.get_or_create(
            asset=asset,
            defaults={"provider": AssetMarketData.Provider.FMP},
        )
        market_data.status = AssetMarketData.Status.STALE
        market_data.last_synced_at = timezone.now()
        market_data.last_error = error_message
        market_data.save()
        asset.is_active = False
        asset.save(update_fields=["is_active", "updated_at"])
        return asset

    @staticmethod
    def sync_symbols(*, symbols: Iterable[str], asset_type_slug: str = "equity") -> dict:
        created_or_updated = 0
        unresolved = 0
        errors = 0

        for symbol in symbols:
            normalized = (symbol or "").strip().upper()
            if not normalized:
                continue

            try:
                PublicAssetSyncService.sync_symbol(
                    symbol=normalized,
                    asset_type_slug=asset_type_slug,
                )
                created_or_updated += 1
            except EmptyProviderResult as exc:
                unresolved += 1
                existing = Asset.objects.filter(
                    owner__isnull=True,
                    asset_type__slug=asset_type_slug,
                    symbol=normalized,
                ).first()
                if existing:
                    PublicAssetSyncService.mark_asset_unresolved(
                        asset=existing,
                        error_message=str(exc),
                    )
            except IntegrationError:
                errors += 1

        return {
            "created_or_updated": created_or_updated,
            "unresolved": unresolved,
            "errors": errors,
        }

    @staticmethod
    @transaction.atomic
    def sync_equity_directory() -> dict:
        asset_type = PublicAssetSyncService._resolve_asset_type(asset_type_slug="equity")
        stock_rows = FMP_PROVIDER.get_stock_list()
        active_symbols = FMP_PROVIDER.get_actively_traded_symbols()

        seen_symbols: set[str] = set()
        created = 0
        updated = 0

        existing_assets = {
            asset.symbol: asset
            for asset in Asset.objects.filter(
                owner__isnull=True,
                asset_type=asset_type,
            )
            if asset.symbol
        }

        for row in stock_rows:
            symbol = row["symbol"]
            seen_symbols.add(symbol)
            is_active = symbol in active_symbols
            defaults = {
                "asset_type": asset_type,
                "owner": None,
                "name": row["name"],
                "description": "",
                "data": {
                    "market_directory": {
                        "exchange": row.get("exchange", ""),
                        "currency": row.get("currency", ""),
                    }
                },
                "is_active": is_active,
            }

            asset = existing_assets.get(symbol)
            if asset is None:
                asset = Asset.objects.create(symbol=symbol, **defaults)
                created += 1
            else:
                asset.name = defaults["name"]
                asset.data = {**asset.data, **defaults["data"]}
                asset.is_active = is_active
                asset.save()
                updated += 1

            market_data, _ = AssetMarketData.objects.get_or_create(
                asset=asset,
                defaults={"provider": AssetMarketData.Provider.FMP},
            )
            market_data.provider = AssetMarketData.Provider.FMP
            market_data.provider_symbol = symbol
            market_data.status = (
                AssetMarketData.Status.TRACKED if is_active else AssetMarketData.Status.STALE
            )
            market_data.last_synced_at = timezone.now()
            if is_active:
                market_data.last_successful_sync_at = market_data.last_synced_at
                market_data.last_error = ""
            market_data.save()

        deactivated = 0
        for symbol, asset in existing_assets.items():
            if symbol in seen_symbols:
                continue
            asset.is_active = False
            asset.save(update_fields=["is_active", "updated_at"])
            market_data, _ = AssetMarketData.objects.get_or_create(
                asset=asset,
                defaults={"provider": AssetMarketData.Provider.FMP},
            )
            market_data.provider_symbol = symbol
            market_data.status = AssetMarketData.Status.STALE
            market_data.last_synced_at = timezone.now()
            market_data.last_error = "Symbol no longer present in FMP stock list."
            market_data.save()
            deactivated += 1

        return {
            "created": created,
            "updated": updated,
            "deactivated": deactivated,
            "active_symbols": len(active_symbols),
            "directory_symbols": len(seen_symbols),
        }

    @staticmethod
    def refresh_quotes_for_assets(*, assets: Iterable[Asset]) -> dict:
        updated = 0
        stale = 0
        errors = 0

        for asset in assets:
            try:
                PublicAssetSyncService.refresh_quote(asset=asset)
                updated += 1
            except EmptyProviderResult as exc:
                PublicAssetSyncService.mark_asset_stale(asset=asset, error_message=str(exc))
                stale += 1
            except IntegrationError as exc:
                market_data, _ = AssetMarketData.objects.get_or_create(
                    asset=asset,
                    defaults={"provider": AssetMarketData.Provider.FMP},
                )
                market_data.last_synced_at = timezone.now()
                market_data.last_error = str(exc)
                market_data.save()
                errors += 1

        return {
            "updated": updated,
            "stale": stale,
            "errors": errors,
        }
