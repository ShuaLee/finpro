from django.db.models import Q

from accounts.models.holding import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


def recalc_holdings_for_fx_pair(from_fx: str, to_fx: str):
    """
    Called when an FX rate changes.

    Finds all holdings whose asset currency matches either side
    of the FX pair, across all asset subtypes, and refreshes SCVs.
    """

    affected = Holding.objects.filter(
        Q(asset__equity__currency__code=from_fx)
        | Q(asset__equity__currency__code=to_fx)

        | Q(asset__crypto__currency__code=from_fx)
        | Q(asset__crypto__currency__code=to_fx)

        | Q(asset__real_estate__currency__code=from_fx)
        | Q(asset__real_estate__currency__code=to_fx)

        | Q(asset__custom__currency__code=from_fx)
        | Q(asset__custom__currency__code=to_fx)

        | Q(asset__commodity__currency__code=from_fx)
        | Q(asset__commodity__currency__code=to_fx)
    ).distinct()

    for holding in affected:
        SCVRefreshService.holding_changed(holding)
