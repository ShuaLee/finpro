from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from assets.models.custom.custom_asset_type import CustomAssetType


class CustomAssetField(models.Model):
    """
    Defines a schema field for a CustomAssetType.
    """

    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    DATE = "date"

    FIELD_TYPES = [
        (TEXT, "Text"),
        (NUMBER, "Decimal"),
        (BOOLEAN, "Boolean"),
        (CHOICE, "Choice"),
        (DATE, "Date"),
    ]

    asset_type = models.ForeignKey(
        CustomAssetType,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    name = models.CharField(
        max_length=100,
        editable=False,
        help_text="Internal field name (auto-generated).",
    )

    label = models.CharField(
        max_length=100,
        help_text="Display label (e.g. 'Grade').",
    )

    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPES,
    )

    required = models.BooleanField(default=False)

    choices = models.JSONField(
        null=True,
        blank=True,
        help_text="Required for choice fields only.",
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

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = slugify(self.label).replace("-", "_")
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

        if self.pk:
            old = CustomAssetField.objects.get(pk=self.pk)
            if (
                (old.name != self.name or old.label != self.label)
                and self.asset_type.assets.exists()
            ):
                raise ValidationError(
                    "Field name and label cannot be changed once assets exist. "
                    "Delete and recreate the field instead."
                )

    def __str__(self):
        return f"{self.asset_type.name}: {self.label}"
