from django.db import models


class AssetSchemaConfig(models.Model):
    """
    Stores custom schema configurations for user-defined asset types.
    """
    asset_type = models.CharField(max_length=100, unique=True)
    config = models.JSONField()  # Holds schema definition
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Schema Config"
        verbose_name_plural = "Asset Schema Configs"

    def __str__(self):
        return f"SchemaConfig: {self.asset_type}"
