from django.db.models import Q

from accounts.models.holdings.holding import Holding
from schemas.services.schema_manager import SchemaManager


def recalc_holdings_for_fx_pair(from_fx: str, to_fx: str):
    """
    Called when an FX rate changes.

    Recompute SCVs for all holdings where:
      - asset.currency == from_ccy
      - asset.currency == to_ccy
    OR     any formulas depend on FX in general.

    This does NOT apply rounding changes to holding models.
    SCVs for holding-sourced values remain untouched.
    """

    # --- 1. Identify affected holdings ---
    affected = Holding.objects.filter(
        Q(asset__currency=from_fx) | Q(asset__currency=to_fx)
    )

    if not affected.exists():
        return

    # --- 2. For each holding, refresh SCVs using schema manager ---
    for holding in affected:
        schema = holding.active_schema
        if not schema:
            continue

        mgr = SchemaManager(schema)
        mgr.sync_for_holding(holding)
