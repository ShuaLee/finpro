"""
Registry mapping asset_type.slug -> sync manager class.

This file is intentionally simple.
Adding a new asset class should only require updating this map.
"""


from sync.services.equity.manager import EquitySyncManager

# ---------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------

SYNC_MANAGER_REGISTRY: dict[str, type] = {
    "equity": EquitySyncManager,
}
