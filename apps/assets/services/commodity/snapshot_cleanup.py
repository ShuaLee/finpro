from assets.models.commodity import CommodityAsset, CommoditySnapshotID
from assets.services.base.snapshot_cleanup_base import SnapshotCleanupBaseService


class CommoditySnapshotCleanupService(SnapshotCleanupBaseService):
    asset_extension_model = CommodityAsset
    snapshot_id_model = CommoditySnapshotID
    name_attr = "symbol"   # or "name" if you have one
    currency_attr = "currency"
