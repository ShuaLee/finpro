from assets.models.equity import EquityAsset, EquitySnapshotID
from assets.services.base.snapshot_cleanup_base import SnapshotCleanupBaseService


class EquitySnapshotCleanupService(SnapshotCleanupBaseService):
    asset_extension_model = EquityAsset
    snapshot_id_model = EquitySnapshotID
    name_attr = "ticker"
    currency_attr = "currency"
