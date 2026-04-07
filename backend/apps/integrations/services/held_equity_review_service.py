from difflib import SequenceMatcher

from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset, AssetMarketData
from apps.integrations.exceptions import EmptyProviderResult, IntegrationError
from apps.integrations.models import ActiveEquityListing
from apps.integrations.providers.fmp import FMP_PROVIDER


class HeldEquityReviewService:
    @staticmethod
    def _normalized_name(value: str) -> str:
        return " ".join((value or "").strip().upper().split())

    @staticmethod
    def _names_are_consistent(left: str, right: str) -> bool:
        a = HeldEquityReviewService._normalized_name(left)
        b = HeldEquityReviewService._normalized_name(right)
        if not a or not b:
            return False
        if a == b:
            return True
        if a in b or b in a:
            return True
        return SequenceMatcher(None, a, b).ratio() >= 0.85

    @staticmethod
    def _active_listing_for_symbol(symbol: str):
        normalized = (symbol or "").strip().upper()
        if not normalized:
            return None
        return ActiveEquityListing.objects.filter(provider="fmp", symbol=normalized).first()

    @staticmethod
    def _candidate_rows_from_identifiers(market_data: AssetMarketData) -> list[dict]:
        candidates: list[dict] = []
        seen_keys: set[tuple[str, str]] = set()

        def add_rows(rows):
            for row in rows or []:
                symbol = (row.get("symbol") or "").strip().upper()
                name = (row.get("name") or row.get("companyName") or "").strip()
                if not symbol:
                    continue
                key = (symbol, name)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                candidates.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "exchange": (row.get("exchange") or row.get("exchangeShortName") or "").strip(),
                        "isin": (row.get("isin") or "").strip().upper(),
                        "cusip": (row.get("cusip") or "").strip().upper(),
                        "cik": (row.get("cik") or "").strip(),
                    }
                )

        if market_data.isin:
            add_rows(FMP_PROVIDER.search_by_isin(market_data.isin))
        if market_data.cusip:
            add_rows(FMP_PROVIDER.search_by_cusip(market_data.cusip))
        if market_data.cik:
            add_rows(FMP_PROVIDER.search_by_cik(market_data.cik))

        return candidates

    @staticmethod
    def _resolve_candidate(asset: Asset, market_data: AssetMarketData) -> dict | None:
        candidates = HeldEquityReviewService._candidate_rows_from_identifiers(market_data)
        expected_name = market_data.last_seen_name or asset.name
        expected_exchange = market_data.last_seen_exchange

        matched: list[dict] = []
        for candidate in candidates:
            if not ActiveEquityListing.objects.filter(
                provider="fmp",
                symbol=candidate["symbol"],
            ).exists():
                continue

            if not HeldEquityReviewService._names_are_consistent(expected_name, candidate["name"]):
                continue

            if expected_exchange and candidate["exchange"] and candidate["exchange"] != expected_exchange:
                continue

            matched.append(candidate)

        if len(matched) == 1:
            return matched[0]
        return None

    @staticmethod
    def _mark_review_needed(asset: Asset, market_data: AssetMarketData, reason: str) -> None:
        market_data.status = AssetMarketData.Status.NEEDS_REVIEW
        market_data.last_synced_at = timezone.now()
        market_data.last_error = reason
        market_data.save()

    @staticmethod
    def _mark_stale(asset: Asset, market_data: AssetMarketData, reason: str) -> None:
        market_data.status = AssetMarketData.Status.STALE
        market_data.last_synced_at = timezone.now()
        market_data.last_error = reason
        market_data.save()
        asset.is_active = False
        asset.save(update_fields=["is_active", "updated_at"])

    @staticmethod
    @transaction.atomic
    def enrich_identity(*, asset: Asset) -> AssetMarketData:
        market_data = getattr(asset, "market_data", None)
        if market_data is None:
            market_data = AssetMarketData(asset=asset, provider=AssetMarketData.Provider.FMP)

        profile = FMP_PROVIDER.get_profile_with_identifiers(asset.symbol or market_data.provider_symbol)
        company = profile["company"]
        identifiers = profile["identifiers"]

        market_data.provider_symbol = company["symbol"]
        market_data.last_seen_symbol = company["symbol"]
        market_data.last_seen_name = company["name"]
        market_data.last_seen_exchange = company["exchange"]
        market_data.isin = identifiers.get("isin", "")
        market_data.cusip = identifiers.get("cusip", "")
        market_data.cik = identifiers.get("cik", "")
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = timezone.now()
        market_data.last_successful_sync_at = market_data.last_synced_at
        market_data.last_error = ""
        market_data.save()

        asset.symbol = company["symbol"]
        asset.name = company["name"]
        asset.data = {
            **asset.data,
            "market_profile": {
                "exchange": company["exchange"],
                "currency": company["currency"],
                "country": company["country"],
                "sector": company["sector"],
                "industry": company["industry"],
            },
        }
        asset.save()
        return market_data

    @staticmethod
    def review_asset(*, asset: Asset) -> str:
        market_data = getattr(asset, "market_data", None)
        if market_data is None or not market_data.provider_symbol:
            return "skipped"

        active_listing = HeldEquityReviewService._active_listing_for_symbol(market_data.provider_symbol)
        expected_name = market_data.last_seen_name or asset.name

        if active_listing and HeldEquityReviewService._names_are_consistent(
            expected_name,
            active_listing.name,
        ):
            market_data.status = AssetMarketData.Status.TRACKED
            market_data.last_seen_name = active_listing.name
            market_data.last_seen_symbol = active_listing.symbol
            market_data.last_synced_at = timezone.now()
            market_data.last_error = ""
            market_data.save()
            return "tracked"

        if not any([market_data.isin, market_data.cusip, market_data.cik]):
            HeldEquityReviewService._mark_review_needed(
                asset,
                market_data,
                "Ticker or name changed and no identifiers are stored for verification.",
            )
            return "needs_review"

        try:
            candidate = HeldEquityReviewService._resolve_candidate(asset, market_data)
        except EmptyProviderResult:
            candidate = None
        except IntegrationError as exc:
            HeldEquityReviewService._mark_review_needed(asset, market_data, str(exc))
            return "needs_review"

        if candidate is None:
            HeldEquityReviewService._mark_stale(
                asset,
                market_data,
                "No clear active match found from stored identifiers.",
            )
            return "stale"

        market_data.provider_symbol = candidate["symbol"]
        market_data.last_seen_symbol = candidate["symbol"]
        market_data.last_seen_name = candidate["name"]
        market_data.last_seen_exchange = candidate["exchange"]
        market_data.status = AssetMarketData.Status.TRACKED
        market_data.last_synced_at = timezone.now()
        market_data.last_successful_sync_at = market_data.last_synced_at
        market_data.last_error = ""
        market_data.save()

        asset.symbol = candidate["symbol"]
        asset.name = candidate["name"]
        asset.is_active = True
        asset.save(update_fields=["symbol", "name", "is_active", "updated_at"])
        return "tracked"

    @staticmethod
    def review_all_tracked_equities() -> dict:
        queryset = Asset.objects.filter(
            owner__isnull=True,
            asset_type__slug="equity",
            market_data__provider=AssetMarketData.Provider.FMP,
        ).select_related("market_data", "asset_type")

        summary = {"tracked": 0, "needs_review": 0, "stale": 0, "skipped": 0}
        for asset in queryset:
            result = HeldEquityReviewService.review_asset(asset=asset)
            summary[result] = summary.get(result, 0) + 1
        return summary
