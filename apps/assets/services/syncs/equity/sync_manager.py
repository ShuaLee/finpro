import logging

from django.db import transaction

from assets.models.asset_core import Asset, AssetType, AssetIdentifier
from assets.models.profiles import EquityProfile
from assets.services.syncs.base import BaseSyncService
from assets.services.syncs.equity.identifier_sync_service import EquityIdentifierSyncService
from assets.services.syncs.equity.profile_sync_service import EquityProfileSyncService
from assets.services.syncs.equity.price_sync_service import EquityPriceSyncService
from assets.services.syncs.equity.dividend_sync_service import EquityDividendSyncService
from assets.services.utils import hydrate_identifiers
from external_data.fmp.equities.fetchers import (
    fetch_actively_trading_list,
    fetch_equity_by_cik,
    fetch_equity_by_cusip,
    fetch_equity_by_isin,
    fetch_equity_list,
)

logger = logging.getLogger(__name__)


class EquitySyncManager(BaseSyncService):
    """
    Full synchronization manager for equities.

    Runs sync steps in correct dependency order:

        1. identifiers (ticker, ISIN, CUSIP…)
        2. profile (sector, industry, exchange, metadata…)
        3. price (asset_price + equity price extension)
        4. dividends

    Also includes universe-level synchronization using the FMP stock list.
    """

    COMPONENTS = {
        "identifiers": EquityIdentifierSyncService,
        "profile":     EquityProfileSyncService,
        "price":       EquityPriceSyncService,
        "dividends":   EquityDividendSyncService,
    }

    @transaction.atomic
    def sync(asset: Asset, components: list[str] | None = None) -> dict:
        """
        Perform a full or partial sync.

        components:
            None → run all components
            ["price"], ["profile", "dividends"], etc.
        """

        if asset.asset_type.slug != "equity":
            raise ValueError("EquitySyncManager called on non-equity asset")

        results = {}

        ordered = components or list(EquitySyncManager.COMPONENTS.keys())

        # Always run identifiers first if included
        if "identifiers" in ordered:
            ordered = ["identifiers"] + \
                [c for c in ordered if c != "identifiers"]

        for name in ordered:
            service_cls = EquitySyncManager.COMPONENTS.get(name)
            if not service_cls:
                results[name] = {"success": False,
                                 "reason": "unknown_component"}
                continue

            try:
                logger.info(
                    f"[EQUITY_SYNC] Running {name} for asset {asset.id}")
                result = service_cls().sync(asset)
                if isinstance(result, dict):
                    results[name] = result
                else:
                    results[name] = {"success": bool(result)}

            except Exception as e:
                logger.exception(
                    f"[EQUITY_SYNC] {name} failed for {asset.id}: {e}")
                results[name] = {"success": False, "error": str(e)}

        return results

    # ------------------------------------------------------------
    # UNIVERSE SYNC USING FMP STOCK-LIST
    # ------------------------------------------------------------
    @staticmethod
    @transaction.atomic
    def sync_universe(dry_run: bool = False) -> dict:
        """
        Sync the complete equity universe.

        Steps:
            1) Fetch FMP ticker list
            2) Match against DB
            3) Detect renames via ISIN/CUSIP/CIK
            4) Create new assets
            5) Mark delisted assets
        """

        results = {
            "created": 0,
            "renamed": 0,
            "existing": 0,
            "delisted": 0,
        }

        equity_type = AssetType.objects.get(slug="equity")

        # ------------------------------------------------------------
        # 1. Load FMP universe
        # ------------------------------------------------------------
        fmp_list = fetch_equity_list() or []
        fmp_symbols = {row["symbol"].upper(): row for row in fmp_list}

        logger.info(f"[UNIVERSE] Fetched {len(fmp_list)} symbols")

        # Actively trading
        active_set = fetch_actively_trading_list()

        # ------------------------------------------------------------
        # 2. Index DB assets
        # ------------------------------------------------------------
        db_assets = (
            Asset.objects.filter(asset_type=equity_type)
            .select_related("equity_profile")
            .prefetch_related("identifiers")
        )

        db_by_ticker = {}
        db_by_isin = {}
        db_by_cusip = {}
        db_by_cik = {}

        for asset in db_assets:
            for ident in asset.identifiers.all():
                if ident.id_type == AssetIdentifier.IdentifierType.TICKER:
                    db_by_ticker[ident.value.upper()] = asset
                elif ident.id_type == AssetIdentifier.IdentifierType.ISIN:
                    db_by_isin[ident.value] = asset
                elif ident.id_type == AssetIdentifier.IdentifierType.CUSIP:
                    db_by_cusip[ident.value] = asset
                elif ident.id_type == AssetIdentifier.IdentifierType.CIK:
                    db_by_cik[ident.value] = asset

        # ------------------------------------------------------------
        # 3. Process all FMP tickers
        # ------------------------------------------------------------
        seen_assets = set()

        for symbol, row in fmp_symbols.items():
            company_name = row.get("companyName")

            # --------------------------------------------------------
            # CASE A — Ticker already exists
            # --------------------------------------------------------
            if symbol in db_by_ticker:
                asset = db_by_ticker[symbol]
                seen_assets.add(asset.id)
                results["existing"] += 1

                # update company name if changed
                if asset.equity_profile.name != company_name:
                    asset.equity_profile.name = company_name
                    if not dry_run:
                        asset.equity_profile.save()

                # update actively trading flag
                is_active = symbol in active_set
                if asset.equity_profile.is_actively_trading != is_active:
                    asset.equity_profile.is_actively_trading = is_active
                    if not dry_run:
                        asset.equity_profile.save()

                continue

            # --------------------------------------------------------
            # CASE B — Ticker not found → attempt identifier-based match
            # --------------------------------------------------------
            matched_asset = None

            # 1) Try ISIN lookup
            lookup = fetch_equity_by_isin(
                row.get("isin")) if row.get("isin") else None
            if lookup and lookup.get("symbol"):
                ident_symbol = lookup["symbol"].upper()
                matched_asset = db_by_ticker.get(ident_symbol)

            # 2) Try CUSIP
            if not matched_asset and row.get("cusip"):
                lookup = fetch_equity_by_cusip(row.get("cusip"))
                if lookup and lookup.get("symbol"):
                    ident_symbol = lookup["symbol"].upper()
                    matched_asset = db_by_ticker.get(ident_symbol)

            # 3) Try CIK
            if not matched_asset and row.get("cik"):
                lookup = fetch_equity_by_cik(row.get("cik"))
                if lookup and lookup.get("symbol"):
                    ident_symbol = lookup["symbol"].upper()
                    matched_asset = db_by_ticker.get(ident_symbol)

            if matched_asset:
                # rename case
                old_ticker = matched_asset.primary_ticker
                results["renamed"] += 1

                if not dry_run:
                    # deactivate old ticker
                    matched_asset.identifiers.filter(
                        id_type=AssetIdentifier.IdentifierType.TICKER,
                        is_primary=True,
                    ).update(is_primary=False)

                    # assign new ticker
                    AssetIdentifier.objects.create(
                        asset=matched_asset,
                        id_type=AssetIdentifier.IdentifierType.TICKER,
                        value=symbol,
                        is_primary=True,
                    )

                    hydrate_identifiers(
                        matched_asset, lookup.get("identifiers", {}))

                seen_assets.add(matched_asset.id)
                continue

            # --------------------------------------------------------
            # CASE C — brand new asset
            # --------------------------------------------------------
            if dry_run:
                results["created"] += 1
                continue

            asset = Asset.objects.create(
                asset_type=equity_type,
            )

            AssetIdentifier.objects.create(
                asset=asset,
                id_type=AssetIdentifier.IdentifierType.TICKER,
                value=symbol,
                is_primary=True,
            )

            EquityProfile.objects.create(
                asset=asset,
                name=company_name,
                is_actively_trading=(symbol in active_set),
            )

            results["created"] += 1
            seen_assets.add(asset.id)

        # ------------------------------------------------------------
        # 4. Mark delisted assets
        # ------------------------------------------------------------
        for asset in db_assets:
            if asset.id not in seen_assets:
                results["delisted"] += 1
                if not dry_run:
                    asset.equity_profile.is_actively_trading = False
                    asset.equity_profile.save()

        return results
