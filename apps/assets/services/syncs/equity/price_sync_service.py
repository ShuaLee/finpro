import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.pricing import AssetPrice
from assets.models.pricing.extensions import EquityPriceExtension
from assets.services.utils import get_primary_ticker
from assets.services.dividends.recompute import recompute_dividend_extension
from external_data.fmp.equities.fetchers import fetch_equity_quote

logger = logging.getLogger(__name__)


class EquityPriceSyncService:
    """
    Syncs:
      - AssetPrice.price
      - EquityPriceExtension.change
      - EquityPriceExtension.volume

    IMPORTANT:
    Any price change MUST trigger dividend yield recomputation.
    """

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity"}

        ticker = get_primary_ticker(asset)
        if not ticker:
            return {"success": False, "error": "no_ticker"}

        data = fetch_equity_quote(ticker)
        if not data:
            EquityPriceSyncService._mark_asset_inactive(asset)
            return {"success": False, "error": "no_data"}

        return EquityPriceSyncService._apply_price_fields(asset, data)

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
        # 🔁 CRITICAL: price change affects dividend yield
        # --------------------------------------------------
        recompute_dividend_extension(asset)

        return {
            "success": True,
            "fields": report,
        }

    @staticmethod
    def _mark_asset_inactive(asset: Asset):
        profile = getattr(asset, "equity_profile", None)
        if profile and profile.is_actively_trading:
            profile.is_actively_trading = False
            profile.save()
