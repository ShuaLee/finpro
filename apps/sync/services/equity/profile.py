import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.profiles.equity_profile import EquityProfile
from assets.models.classifications.sector import Sector
from assets.models.classifications.industry import Industry
from assets.models.exchanges import Exchange
from fx.services.utils import resolve_fx_currency, resolve_country
from external_data.providers.fmp.client import FMP_PROVIDER
from external_data.exceptions import ExternalDataError
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class EquityProfileSyncService(BaseSyncService):
    """
    Syncs equity profile metadata from the provider.

    Responsibilities:
    - Update EquityProfile fields
    - Update Asset currency
    - Update is_actively_trading flag

    Does NOT:
    - Change tickers
    - Handle renames
    - Touch identifiers
    """

    name = "equity.profile"

    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity_asset"}

        ticker = asset.primary_identifier.value
        provider = FMP_PROVIDER

        try:
            identity = provider.get_equity_identity(ticker)
        except ExternalDataError:
            raise

        profile_data = identity.profile

        profile, _ = EquityProfile.objects.get_or_create(asset=asset)

        changes: dict[str, str] = {}

        # --------------------------------------------------
        # Simple scalar fields
        # --------------------------------------------------
        def apply(field, value):
            old = getattr(profile, field)
            if value is None:
                return
            if old != value:
                setattr(profile, field, value)
                changes[field] = "updated"
            else:
                changes[field] = "unchanged"

        apply("name", profile_data.get("name"))
        apply("website", profile_data.get("website"))
        apply("description", profile_data.get("description"))
        apply("image_url", profile_data.get("image_url"))
        apply("market_cap", profile_data.get("market_cap"))
        apply("beta", profile_data.get("beta"))
        apply("last_dividend", profile_data.get("last_dividend"))
        apply("ipo_date", profile_data.get("ipo_date"))

        # --------------------------------------------------
        # Flags
        # --------------------------------------------------
        for flag in (
            "is_etf",
            "is_adr",
            "is_fund",
            "is_actively_trading",
        ):
            if flag in profile_data:
                new = bool(profile_data[flag])
                old = getattr(profile, flag)
                if new != old:
                    setattr(profile, flag, new)
                    changes[flag] = "updated"
                else:
                    changes[flag] = "unchanged"

        # --------------------------------------------------
        # Relationships
        # --------------------------------------------------
        if sector := profile_data.get("sector"):
            sec, _ = Sector.objects.get_or_create(name=sector)
            if profile.sector != sec:
                profile.sector = sec
                changes["sector"] = "updated"

        if industry := profile_data.get("industry"):
            ind, _ = Industry.objects.get_or_create(name=industry)
            if profile.industry != ind:
                profile.industry = ind
                changes["industry"] = "updated"

        if exch_code := profile_data.get("exchange"):
            exch, _ = Exchange.objects.get_or_create(code=exch_code)
            if profile.exchange != exch:
                profile.exchange = exch
                changes["exchange"] = "updated"

        if country := profile_data.get("country"):
            resolved = resolve_country(country)
            if profile.country != resolved:
                profile.country = resolved
                changes["country"] = "updated"

        # --------------------------------------------------
        # Asset currency
        # --------------------------------------------------
        if currency := profile_data.get("currency"):
            try:
                fx = resolve_fx_currency(currency)
                if asset.currency != fx:
                    asset.currency = fx
                    asset.save(update_fields=["currency"])
                    changes["currency"] = "updated"
            except Exception:
                logger.warning(
                    "[PROFILE_SYNC] Failed to resolve currency %s", currency
                )
                changes["currency"] = "failed"

        profile.save()

        return {
            "success": True,
            "fields": changes,
            "is_actively_trading": profile.is_actively_trading,
        }
