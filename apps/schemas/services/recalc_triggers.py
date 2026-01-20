from django.db.models import Q

from accounts.models.holding import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


def recalc_holdings_for_fx_pair(from_fx: str, to_fx: str):
    """
    Called when an FX rate changes.

    FX changes affect displayed values, NOT holdings themselves.
    We therefore route through SCVRefreshService to ensure:
      - user overrides are respected
      - formulas recompute
      - asset + FX-backed SCVs refresh
    """

    affected = Holding.objects.filter(
        Q(asset__currency=from_fx) | Q(asset__currency=to_fx)
    )

    for holding in affected:
        # SCVRefreshService already handles:
        # - schema existence
        # - recompute rules
        SCVRefreshService.holding_changed(holding)
