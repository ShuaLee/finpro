import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetType, AssetIdentifier
from assets.models.profiles import EquityProfile
from assets.services.syncs.base import BaseSyncService
from assets.services.syncs.equity.identifier_sync_service import (
    EquityIdentifierSyncService,
)
from assets.services.syncs.equity.profile_sync_service import (
    EquityProfileSyncService,
)
from assets.services.syncs.equity.price_sync_service import (
    EquityPriceSyncService,
)
from assets.services.syncs.equity.dividend_sync_service import (
    EquityDividendSyncService,
)
from assets.services.utils import hydrate_identifiers
from external_data.fmp.equities.fetchers import (
    fetch_actively_trading_list,
    fetch_equity_profile,
    fetch_equity_list,
)

logger = logging.getLogger(__name__)


class EquitySyncManager(BaseSyncService):
    """
    Full synchronization manager for equities.
    """

    COMPONENTS = {
        "identifiers": EquityIdentifierSyncService,
        "profile": EquityProfileSyncService,
        "price": EquityPriceSyncService,
        "dividends": EquityDividendSyncService,
    }

    # ============================================================
    # INDIVIDUAL ASSET SYNC
    # ============================================================
    @staticmethod
    @transaction.atomic
    def sync(asset: Asset, components: list[str] | None = None) -> dict:
        if asset.asset_type.slug != "equity":
            raise ValueError("EquitySyncManager called on non-equity asset")

        results: dict = {}

        ordered = components or list(EquitySyncManager.COMPONENTS.keys())

        # identifiers must always run first
        if "identifiers" in ordered:
            ordered = ["identifiers"] + [
                c for c in ordered if c != "identifiers"
            ]

        for name in ordered:
            service_cls = EquitySyncManager.COMPONENTS.get(name)
            if not service_cls:
                results[name] = {
                    "success": False,
                    "error": "unknown_component",
                }
                continue

            try:
                logger.info(
                    f"[EQUITY_SYNC] Running {name} for asset {asset.id}"
                )
                result = service_cls().sync(asset)
                results[name] = result or {"success": True}

            except Exception as exc:
                logger.exception(
                    f"[EQUITY_SYNC] {name} failed for {asset.id}: {exc}"
                )
                results[name] = {
                    "success": False,
                    "error": str(exc),
                }

        return results

    # ============================================================
    # UNIVERSE SYNC
    # ============================================================
    @staticmethod
    @transaction.atomic
    def sync_universe(dry_run: bool = False) -> dict:
        """
        Authoritative equity universe sync using FMP stock-list.
        """

        results = {
            "created": 0,
            "renamed": 0,
            "existing": 0,
            "delisted": 0,
        }

        equity_type = AssetType.objects.get(slug="equity")

        if not Asset.objects.filter(asset_type=equity_type).exists():
            raise RuntimeError(
                "Equity universe not seeded. "
                "Run `manage.py seed_equities` before `sync_equities --universe`."
            )

        identifier_service = EquityIdentifierSyncService()

        # ------------------------------------------------------------
        # 1. Load FMP universe
        # ------------------------------------------------------------
        fmp_list = fetch_equity_list() or []
        fmp_symbols = {row["symbol"].upper(): row for row in fmp_list}

        logger.info(f"[UNIVERSE] Fetched {len(fmp_symbols)} symbols")

        active_set = fetch_actively_trading_list() or set()

        # ------------------------------------------------------------
        # 2. Index DB assets by PRIMARY ticker only
        # ------------------------------------------------------------
        db_assets = (
            Asset.objects.filter(asset_type=equity_type)
            .select_related("equity_profile")
            .prefetch_related("identifiers")
        )

        db_by_primary_ticker: dict[str, Asset] = {}

        for asset in db_assets:
            for ident in asset.identifiers.all():
                if (
                    ident.id_type == AssetIdentifier.IdentifierType.TICKER
                    and ident.is_primary
                ):
                    db_by_primary_ticker[ident.value.upper()] = asset

        seen_asset_ids: set[str] = set()

        # ------------------------------------------------------------
        # 3. Process FMP symbols
        # ------------------------------------------------------------
        for symbol, row in fmp_symbols.items():
            company_name = row.get("companyName")
            is_active = symbol in active_set

            # --------------------------------------------------------
            # CASE A — direct primary ticker match
            # --------------------------------------------------------
            asset = db_by_primary_ticker.get(symbol)
            if asset:
                seen_asset_ids.add(asset.id)
                results["existing"] += 1

                if not dry_run:
                    profile = asset.equity_profile
                    if profile.name != company_name:
                        profile.name = company_name
                    if profile.is_actively_trading != is_active:
                        profile.is_actively_trading = is_active
                    profile.save()

                continue

            # --------------------------------------------------------
            # CASE B — identity recovery via identifiers
            # --------------------------------------------------------
            profile_data = fetch_equity_profile(symbol)
            matched_asset = None

            if profile_data and "identifiers" in profile_data:
                identifiers = profile_data["identifiers"]

                for id_type in (
                    AssetIdentifier.IdentifierType.ISIN,
                    AssetIdentifier.IdentifierType.CUSIP,
                    AssetIdentifier.IdentifierType.CIK,
                ):
                    value = identifiers.get(id_type)
                    if not value:
                        continue

                    matched_asset = Asset.objects.filter(
                        asset_type=equity_type,
                        identifiers__id_type=id_type,
                        identifiers__value=value,
                    ).first()

                    if matched_asset:
                        break

            if matched_asset:
                results["renamed"] += 1
                seen_asset_ids.add(matched_asset.id)

                if not dry_run:
                    identifier_service._set_primary_ticker(
                        matched_asset, symbol
                    )

                    hydrate_identifiers(
                        matched_asset,
                        profile_data.get("identifiers", {}),
                    )

                    profile = matched_asset.equity_profile
                    if profile.name != company_name:
                        profile.name = company_name
                    profile.is_actively_trading = is_active
                    profile.save()

                continue

            # --------------------------------------------------------
            # CASE C — brand new asset
            # --------------------------------------------------------
            results["created"] += 1
            if dry_run:
                continue

            asset = Asset.objects.create(asset_type=equity_type)

            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
                is_primary=True,
            )

            EquityProfile.objects.create(
                asset=asset,
                name=company_name,
                is_actively_trading=is_active,
            )

            seen_asset_ids.add(asset.id)

        # ------------------------------------------------------------
        # 4. Delist missing assets (safe only)
        # ------------------------------------------------------------
        for asset in db_assets:
            if asset.id not in seen_asset_ids:
                if asset.identifiers.filter(
                    id_type__in=[
                        AssetIdentifier.IdentifierType.ISIN,
                        AssetIdentifier.IdentifierType.CIK,
                    ]
                ).exists():
                    results["delisted"] += 1
                    if not dry_run:
                        asset.equity_profile.is_actively_trading = False
                        asset.equity_profile.save()

        return results

    @staticmethod
    @transaction.atomic
    def seed_universe() -> dict:
        equity_type = AssetType.objects.get(slug="equity")

        fmp_list = fetch_equity_list() or []
        active_set = fetch_actively_trading_list() or set()

        existing = set(
            AssetIdentifier.objects.filter(
                id_type=AssetIdentifier.IdentifierType.TICKER,
                is_primary=True,
            ).values_list("value", flat=True)
        )

        created = 0

        for row in fmp_list:
            symbol = row["symbol"].upper()
            name = row.get("companyName")

            if symbol in existing:
                continue

            asset = Asset.objects.create(asset_type=equity_type)

            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
                is_primary=True,
            )

            EquityProfile.objects.create(
                asset=asset,
                name=name,
                is_actively_trading=(symbol in active_set),
            )

            created += 1

        return {"created": created}
