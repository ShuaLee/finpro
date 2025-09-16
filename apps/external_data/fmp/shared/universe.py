import requests
import logging
from django.conf import settings

from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType

logger = logging.getLogger(__name__)
FMP_API_KEY = settings.FMP_API_KEY
FMP_BASE = "https://financialmodelingprep.com/api/v3"


def fetch_equity_universe() -> list[dict]:
    """Fetch all listed equities (symbol + metadata)."""
    url = f"{FMP_BASE}/stock/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch equity universe: {e}")
        return []


def seed_equity_universe(universe_data: list[dict]) -> dict:
    """
    universe_data = output from FMP /stock/list
    Inserts new equities into DB with IPO status.
    """
    created, existing = 0, 0

    for record in universe_data:
        symbol = record.get("symbol")
        name = record.get("name") or symbol
        exchange = record.get("exchangeShortName")

        asset, was_created = Asset.objects.get_or_create(
            asset_type=DomainType.EQUITY,
            symbol=symbol,
            defaults={"name": name},
        )

        if was_created:
            # Create detail stub with IPO status
            EquityDetail.objects.create(
                asset=asset,
                exchange=exchange,
                listing_status="IPO",  # 🔑 IPO until first successful quote
                is_custom=False,
            )
            created += 1
        else:
            existing += 1

    return {"created": created, "existing": existing}


def fetch_crypto_universe() -> list[dict]:
    """Fetch all supported cryptos."""
    url = f"{FMP_BASE}/cryptocurrency/list?apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json() or []
    except Exception as e:
        logger.error(f"Failed to fetch crypto universe: {e}")
        return []
