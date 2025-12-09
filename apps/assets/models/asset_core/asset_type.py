from django.core.exceptions import ValidationError
from django.db import models

from users.models.profile import Profile


class AssetType(models.Model):
    slug = models.SlugField(unique=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    # Identifier rules for this asset type
    identifier_rules = models.JSONField(
        default=list,
        blank=True,
        help_text="Allowed identifier types (e.g., TICKER, ISIN, BASE_SYMBOL)",
    )

    # Whether user can delete it or not
    is_system = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System AssetTypes cannot be deleted.")
        super().delete(*args, **kwargs)
