from assets.models.crypto import CryptoAsset, CryptoSnapshotID
from assets.services.base.snapshot_cleanup_base import SnapshotCleanupBaseService


class CryptoSnapshotCleanupService(SnapshotCleanupBaseService):
    extension_model = CryptoAsset
    snapshot_model = CryptoSnapshotID
    name_attr = "base_symbol"
    currency_attr = "currency"
