from assets.models.crypto import CryptoAsset, CryptoSnapshotID
from assets.services.base.snapshot_cleanup_base import SnapshotCleanupBaseService


class CryptoSnapshotCleanupService(SnapshotCleanupBaseService):
    asset_extension_model = CryptoAsset
    snapshot_id_model = CryptoSnapshotID
    name_attr = "symbol"
    currency_attr = "currency"
