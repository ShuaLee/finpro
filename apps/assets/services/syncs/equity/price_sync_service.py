import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.pricing import AssetPrice
from assets.models.pricing.extensions import EquityPriceExtension
from assets.services.utils import get_primary_ticker
from assets.services.dividends.recompute import recompute_dividend_extension
from assets.services.syncs.equity.identifier_sync_service import (
    EquityIdentifierSyncService,
)
from external_data.fmp.equities.fetchers import (
    fetch_equity_quote,
    fetch_equity_profile,
)

logger = logging.getLogger(__name__)


class EquityPriceSyncService:
    """
    Syncs:
      - AssetPrice.price
      - EquityPriceExtension.change
      - EquityPriceExtension.volume

    Defensive behavior:
      - attempts identity repair on quote failure
      - retries quote once
      - marks inactive only as a last resort
    """

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity"}

        ticker = get_primary_ticker(asset)
        if not ticker:
            return {"success": False, "error": "no_ticker"}

        # --------------------------------------------------
        # 1️⃣ Primary quote attempt
        # --------------------------------------------------
        data = fetch_equity_quote(ticker)
        if data:
            return EquityPriceSyncService._apply_price_fields(asset, data)

        logger.warning(
            "[PRICE_SYNC] Quote failed for %s — attempting identity repair",
            ticker,
        )

        # --------------------------------------------------
        # 2️⃣ Identity repair via profile
        # --------------------------------------------------
        profile = fetch_equity_profile(ticker)
        if profile and "identifiers" in profile:
            EquityIdentifierSyncService().sync(asset)

            # retry with updated ticker
            new_ticker = get_primary_ticker(asset)
            if new_ticker and new_ticker != ticker:
                data = fetch_equity_quote(new_ticker)
                if data:
                    logger.info(
                        "[PRICE_SYNC] Quote recovered after ticker repair: %s → %s",
                        ticker,
                        new_ticker,
                    )
                    return EquityPriceSyncService._apply_price_fields(
                        asset, data
                    )

        # --------------------------------------------------
        # 3️⃣ Final failure → mark inactive
        # --------------------------------------------------
        logger.error(
            "[PRICE_SYNC] Quote permanently failed for asset %s — marking inactive",
            asset.id,
        )
        EquityPriceSyncService._mark_asset_inactive(asset)

        return {"success": False, "error": "quote_failed"}

    # --------------------------------------------------
    # Price application
    # --------------------------------------------------
    @staticmethod
    def _apply_price_fields(asset: Asset, quote: dict) -> dict:
        report = {
            "price": None,
            "change": None,
            "volume": None,
        }

        # -----------------------
        # AssetPrice
        # -----------------------
        asset_price, _ = AssetPrice.objects.get_or_create(
            asset=asset,
            defaults={"price": quote.get("price") or 0, "source": "FMP"},
        )

        old_price = asset_price.price
        new_price = quote.get("price")

        if new_price is None:
            report["price"] = "missing"
        elif old_price != new_price:
            asset_price.price = new_price
            report["price"] = "updated"
        else:
            report["price"] = "unchanged"

        asset_price.source = "FMP"
        asset_price.save()

        # -----------------------
        # EquityPriceExtension
        # -----------------------
        ext, _ = EquityPriceExtension.objects.get_or_create(
            asset_price=asset_price
        )

        def apply(field, key):
            new_val = quote.get(key)
            old_val = getattr(ext, field)

            if new_val is None:
                report[field] = "missing"
                return

            if old_val != new_val:
                setattr(ext, field, new_val)
                report[field] = "updated"
            else:
                report[field] = "unchanged"

        apply("change", "change")
        apply("volume", "volume")

        ext.save()

        # --------------------------------------------------
        # 🔁 Price change affects dividend yields
        # --------------------------------------------------
        recompute_dividend_extension(asset)

        return {
            "success": True,
            "fields": report,
        }

    # --------------------------------------------------
    # Inactive handling
    # --------------------------------------------------
    @staticmethod
    def _mark_asset_inactive(asset: Asset):
        profile = getattr(asset, "equity_profile", None)
        if profile and profile.is_actively_trading:
            profile.is_actively_trading = False
            profile.save()
