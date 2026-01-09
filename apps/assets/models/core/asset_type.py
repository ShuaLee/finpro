from django.core.exceptions import ValidationError
from django.db import models


class AssetType(models.Model):
    """
    Defines the category / behaviour of an Asset.
    System-defined only.
    """

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def delete(self, *args, **kwargs):
        raise ValidationError("AssetTypes are immutable.")
    
    def __str__(self):
        return self.name
