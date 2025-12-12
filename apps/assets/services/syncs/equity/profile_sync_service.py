import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.profiles import EquityProfile
from assets.services.utils import get_primary_ticker, hydrate_identifiers
from external_data.fmp.equities.fetchers import fetch_equity_profile
from fx.services.utils import resolve_country, resolve_fx_currency

logger = logging.getLogger(__name__)


class EquityProfileSyncService:

    # =============================
    # PUBLIC SYNC ENTRYPOINT
    # =============================
    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> bool:
        """
        Syncs ONLY the stable company / profile metadata.
        Does NOT touch price, dividend events, or universe logic.
        """
        if asset.asset_type.slug != "equity":
            return False

        ticker = get_primary_ticker(asset)
        if not ticker:
            logger.warning(f"No ticker for asset {asset.id}")
            return False

        data = fetch_equity_profile(ticker)
        if not data:
            logger.warning(f"No profile returned for {ticker}")
            return False

        profile_data = data.get("profile", {})
        identifiers = data.get("identifiers", {})

        EquityProfileSyncService._apply_profile(asset, profile_data)
        hydrate_identifiers(asset, identifiers)

        return True

    # =============================
    # APPLY PROFILE FIELDS TO ASSET + EQUITYPROFILE
    # =============================
    @staticmethod
    def _apply_profile(asset: Asset, data: dict):

        if not isinstance(data, dict):
            return

        # Ensure profile exists
        profile, _ = EquityProfile.objects.get_or_create(asset=asset)

        # ------------ Name + Currency ------------
        if "name" in data and data["name"]:
            profile.name = data["name"]

        if "currency" in data and data["currency"]:
            try:
                asset.currency = resolve_fx_currency(data["currency"])
            except Exception:
                pass

        # ------------ Website / Description / Image ------------
        for field in ["website", "description", "image_url"]:
            if field in data and data[field]:
                setattr(profile, field, data[field])

        # ------------ Relationships ------------
        if "sector" in data and data["sector"]:
            profile.sector = profile._resolve_sector(data["sector"])

        if "industry" in data and data["industry"]:
            profile.industry = profile._resolve_industry(data["industry"])

        if "exchange" in data and data["exchange"]:
            profile.exchange = profile._resolve_exchange(data["exchange"])

        if "country" in data and data["country"]:
            profile.country = resolve_country(data["country"])

        # ------------ Fundamentals ------------
        for field in ["market_cap", "beta", "last_dividend", "ipo_date"]:
            if field in data and data[field] is not None:
                setattr(profile, field, data[field])

        # ------------ Flags ------------
        for field in ["is_etf", "is_adr", "is_fund", "is_actively_trading"]:
            if field in data and data[field] is not None:
                setattr(profile, field, bool(data[field]))

        asset.save()
        profile.save()
