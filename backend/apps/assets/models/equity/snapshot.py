from django.db import models


class EquitySnapshotID(models.Model):
    """
    Singleton pointer to the active equity snapshot.
    """
    current_snapshot = models.UUIDField()
