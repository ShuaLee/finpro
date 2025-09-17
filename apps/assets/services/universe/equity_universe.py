import logging
from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from external_data.fmp.equities.fetchers import fetch_equity_universe
from external_data.fmp.shared.isin import search_by_isin

logger = logging.getLogger(__name__)


def seed_equity_universe() -> dict:
    """
    Bootstrap the DB with the full FMP equity universe.
    - Inserts everything as ACTIVE.
    - Does not reconcile (first snapshot).
    """
    universe_data = fetch_equity_universe()
    created, existing = 0, 0

    for record in universe_data:
        symbol = record.get("symbol")
        if not symbol:
            continue

        name = record.get("name") or symbol
        exchange = record.get("exchangeShortName")

        asset, was_created = Asset.objects.get_or_create(
            asset_type=DomainType.EQUITY,
            symbol=symbol,
            defaults={"name": name},
        )

        if was_created:
            EquityDetail.objects.create(
                asset=asset,
                exchange=exchange,
                listing_status="ACTIVE",  # 🔑 initial load = ACTIVE
                is_custom=False,
            )
            created += 1
        else:
            existing += 1

    logger.info(
        f"Equity universe seeded. Created={created}, Existing={existing}")
    return {"created": created, "existing": existing}


def sync_equity_universe() -> dict:
    """
    Reconcile DB equities with FMP /stock/list.
    - Phase 1: Reconcile missing tickers (rename vs delist).
    - Phase 2: Insert new tickers as ACTIVE.
    """
    universe_data = fetch_equity_universe()
    fmp_symbols = {
        rec.get("symbol"): rec for rec in universe_data if rec.get("symbol")}

    created, reconciled, flagged_delisted, still_active = 0, 0, 0, 0

    # Phase 1: Reconcile / mark delisted
    db_assets = Asset.objects.filter(
        asset_type=DomainType.EQUITY).select_related("equity_detail")
    for asset in db_assets:
        if asset.symbol not in fmp_symbols:
            detail, _ = EquityDetail.objects.get_or_create(asset=asset)
            reconciled_this = False

            # Try reconciliation by ISIN
            if detail.isin:
                match = search_by_isin(detail.isin)
                if match and match.get("symbol"):
                    new_symbol = match["symbol"]
                    new_name = match.get("name") or asset.name

                    # Avoid duplication: update existing row instead of creating new
                    asset.symbol = new_symbol
                    asset.name = new_name
                    asset.save(update_fields=["symbol", "name"])
                    detail.listing_status = "ACTIVE"
                    detail.save(update_fields=["listing_status"])
                    reconciled += 1
                    reconciled_this = True
                    logger.info(
                        f"Reconciled {asset.id}: {asset.symbol} → {new_symbol}")

            # If reconciliation failed → mark delisted
            if not reconciled_this:
                if detail.listing_status != "DELISTED":
                    detail.listing_status = "DELISTED"
                    detail.save(update_fields=["listing_status"])
                    flagged_delisted += 1
        else:
            still_active += 1

    # Phase 2: Insert brand new tickers
    db_symbols = set(db_assets.values_list("symbol", flat=True))
    for symbol, record in fmp_symbols.items():
        if symbol not in db_symbols:
            name = record.get("name") or symbol
            exchange = record.get("exchangeShortName")

            asset = Asset.objects.create(
                asset_type=DomainType.EQUITY,
                symbol=symbol,
                name=name,
            )
            EquityDetail.objects.create(
                asset=asset,
                exchange=exchange,
                listing_status="ACTIVE",
                is_custom=False,
            )
            created += 1

    logger.info(
        f"Equity universe sync complete. Created={created}, Reconciled={reconciled}, "
        f"Delisted={flagged_delisted}, Still active={still_active}"
    )

    return {
        "created": created,
        "reconciled": reconciled,
        "delisted": flagged_delisted,
        "active": still_active,
    }
