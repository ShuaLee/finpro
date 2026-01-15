from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from assets.models.custom.custom_asset_type import CustomAssetType


class CustomAssetField(models.Model):
    """
    Defines a schema field for a CustomAssetType.
    """

    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Decimal"),
        ("boolean", "Boolean"),
        ("choice", "Choice"),
        ("date", "Date"),
    ]

    asset_type = models.ForeignKey(
        CustomAssetType,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    name = models.CharField(
        max_length=100,
        editable=False,
        help_text="Internal field name (e.g. 'grade', 'card_type').",
    )

    label = models.CharField(
        max_length=100,
        help_text="Display label (e.g. 'Graded Score').",
    )

    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
    )

    required = models.BooleanField(default=False)

    choices = models.JSONField(
        blank=True,
        null=True,
        help_text="Used for choice fields only.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asset_type", "name"],
                name="unique_custom_field_name_per_type",
            ),
            models.UniqueConstraint(
                fields=["asset_type", "label"],
                name="unique_custom_field_label_per_type",
            ),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.label}"
    
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = slugify(self.label).replace("-", "_")
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        if not self.pk:
            return

        old = CustomAssetField.objects.get(pk=self.pk)

        if old.name != self.name or old.label != self.label:
            if self.asset_type.assets.exists():
                raise ValidationError(
                    "Field name and label cannot be changed once assets exist. "
                    "Delete and recreate the field instead."
                )