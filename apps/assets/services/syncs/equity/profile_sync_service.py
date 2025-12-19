import logging

from django.db import transaction

from assets.models.asset_core import Asset
from assets.models.classifications import Industry, Sector
from assets.models.exchanges import Exchange
from assets.models.profiles import EquityProfile
from assets.services.utils import get_primary_ticker, hydrate_identifiers
from external_data.fmp.equities.fetchers import fetch_equity_profile
from fx.services.utils import resolve_country, resolve_fx_currency

logger = logging.getLogger(__name__)


class EquityProfileSyncService:

    FIELD_GROUPS = {
        "simple": ["name", "website", "description", "image_url"],
        "fundamentals": ["market_cap", "beta", "last_dividend", "ipo_date"],
        "flags": ["is_etf", "is_adr", "is_fund", "is_actively_trading"],
    }

    @staticmethod
    @transaction.atomic
    def sync(asset: Asset) -> dict:
        """
        Syncs profile metadata + asset currency.
        Returns a detailed change-report dict.
        """
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity"}

        ticker = get_primary_ticker(asset)
        if not ticker:
            return {"success": False, "error": "missing_ticker"}

        data = fetch_equity_profile(ticker)
        if not data:
            return {"success": False, "error": "no_profile_from_fmp"}

        profile_data = data.get("profile", {})
        identifiers = data.get("identifiers", {})

        report = EquityProfileSyncService._apply_profile(asset, profile_data)

        # Also hydrate identifiers (ISIN / CUSIP / CIK)
        hydrate_identifiers(asset, identifiers)

        return {"success": True, "fields": report}

    # ------------------------------------------------------------
    # PROFILE APPLICATION WITH CHANGE TRACKING
    # ------------------------------------------------------------
    @staticmethod
    def _apply_profile(asset: Asset, data: dict) -> dict:

        changes = {}

        # --------------------------------------------------
        # Ensure profile exists (WITH creation flag)
        # --------------------------------------------------
        profile, created = EquityProfile.objects.get_or_create(
            asset=asset,
            defaults={
                "name": data.get("name") or asset.name,
            },
        )

        # Guarantee name is set (admin visibility)
        if not profile.name:
            profile.name = data.get("name") or asset.name
            changes["name"] = "updated"

        # --------------------------
        # Currency (ON ASSET)
        # --------------------------
        if data.get("currency"):
            try:
                fx_obj = resolve_fx_currency(data["currency"])
                if asset.currency != fx_obj:
                    asset.currency = fx_obj
                    changes["currency"] = "updated"
                else:
                    changes["currency"] = "unchanged"
            except Exception:
                changes["currency"] = "failed"
        elif not created:
            changes["currency"] = "missing"

        # --------------------------
        # Simple direct fields
        # --------------------------
        for field in EquityProfileSyncService.FIELD_GROUPS["simple"]:
            new = data.get(field)
            old = getattr(profile, field)

            if new is None:
                if not created:
                    changes[field] = "missing"
                continue

            if old != new:
                setattr(profile, field, new)
                changes[field] = "updated"
            else:
                changes[field] = "unchanged"

        # --------------------------
        # RELATIONSHIPS
        # --------------------------
        # sector
        sec_name = data.get("sector")
        if sec_name:
            sec, _ = Sector.objects.get_or_create(name=sec_name)
            if profile.sector != sec:
                profile.sector = sec
                changes["sector"] = "updated"
            else:
                changes["sector"] = "unchanged"

        # industry
        ind_name = data.get("industry")
        if ind_name:
            ind, _ = Industry.objects.get_or_create(name=ind_name)
            if profile.industry != ind:
                profile.industry = ind
                changes["industry"] = "updated"
            else:
                changes["industry"] = "unchanged"

        # exchange
        exch_code = data.get("exchange")
        if exch_code:
            ex, _ = Exchange.objects.get_or_create(code=exch_code)
            if profile.exchange != ex:
                profile.exchange = ex
                changes["exchange"] = "updated"
            else:
                changes["exchange"] = "unchanged"

        # country
        if data.get("country"):
            new_country = resolve_country(data["country"])
            if profile.country != new_country:
                profile.country = new_country
                changes["country"] = "updated"
            else:
                changes["country"] = "unchanged"
        elif not created:
            changes["country"] = "missing"

        # --------------------------
        # FUNDAMENTALS
        # --------------------------
        for field in EquityProfileSyncService.FIELD_GROUPS["fundamentals"]:
            new = data.get(field)
            old = getattr(profile, field)

            if new is None:
                if not created:
                    changes[field] = "missing"
                continue

            if old != new:
                setattr(profile, field, new)
                changes[field] = "updated"
            else:
                changes[field] = "unchanged"

        # --------------------------
        # FLAGS
        # --------------------------
        for field in EquityProfileSyncService.FIELD_GROUPS["flags"]:
            if field not in data:
                if not created:
                    changes[field] = "missing"
                continue

            new = bool(data[field])
            old = getattr(profile, field)

            if new != old:
                setattr(profile, field, new)
                changes[field] = "updated"
            else:
                changes[field] = "unchanged"

        asset.save()
        profile.save()

        return changes
