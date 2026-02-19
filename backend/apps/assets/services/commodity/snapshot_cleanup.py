from assets.models.commodity import CommodityAsset, CommoditySnapshotID
from assets.services.base.snapshot_cleanup_base import SnapshotCleanupBaseService


class CommoditySnapshotCleanupService(SnapshotCleanupBaseService):
    extension_model = CommodityAsset
    snapshot_model = CommoditySnapshotID
    name_attr = "symbol"
    currency_attr = "currency"
