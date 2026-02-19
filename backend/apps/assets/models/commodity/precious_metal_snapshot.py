from django.db import models


class PreciousMetalSnapshotID(models.Model):
    """
    Singleton pointer to the active precious metal snapshot.

    Mirrors CommoditySnapshotID / CryptoSnapshotID / EquitySnapshotID exactly.
    """

    current_snapshot = models.UUIDField()

    def __str__(self):
        return f"Active precious metal snapshot: {self.current_snapshot}"
