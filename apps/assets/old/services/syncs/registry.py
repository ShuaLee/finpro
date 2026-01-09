from typing import Dict, Type

from assets.services.syncs.equity import EquitySyncManager
# from ... crypto, real estate, etc.


SYNC_MANAGER_REGISTRY: Dict[str, Type] = {
    "equity": EquitySyncManager,
    # "crypto": CryptoSyncManager,
    # "real_estate": RealEstateSyncManager,
}
