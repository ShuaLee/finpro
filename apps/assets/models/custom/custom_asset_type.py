from django.db import models

from users.models.profile import Profile


class CustomAssetType(models.Model):
    """
    User-defined asset classification and schema.
    """

    name = models.CharField(max_length=100)

    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="custom_asset_types",
    )

    class Meta:
        unique_together = ("name", "created_by")
        ordering = ["name"]

    def __str__(self):
        return self.name
