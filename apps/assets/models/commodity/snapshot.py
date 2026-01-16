from django.db import models


class CommoditySnapshotID(models.Model):
    """
    Singleton pointer to the active commodity snapshot.

    Mirrors CryptoSnapshotID / EquitySnapshotID exactly.
    """

    current_snapshot = models.UUIDField()

    def __str__(self):
        return f"Active commodity snapshot: {self.current_snapshot}"