import logging

from django.db import transaction

from assets.models.asset_core import Asset
from sync.services.base import BaseSyncService

logger = logging.getLogger(__name__)


class EquityPriceSyncService(BaseSyncService):
    """
    Syncs the latest equity price.

    Responsibilities:
    - Fetch quote for ticker
    - Update AssetPrice
    - Soft-signal inactive assets

    Does NOT:
    - Change identifiers
    - Handle renames
    - Guess replacements
    """

    name = "equity.price"

    @transaction.atomic
    def _sync(self, asset: Asset) -> dict:
        if asset.asset_type.slug != "equity":
            return {"success": False, "error": "non_equity_asset"}

        ident = asset.primary_identifier
