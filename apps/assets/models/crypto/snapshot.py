from django.db import models


class CryptoSnapshotID(models.Model):
    """
    Singleton pointer to the active crypto snapshot.

    Mirrors EquitySnapshotID exactly.
    """

    current_snapshot = models.UUIDField()

    def __str__(self):
        return f"Active crypto snapshot: {self.current_snapshot}"
