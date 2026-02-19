from django.db import models
from django.core.exceptions import ValidationError


class SchemaColumnCategory(models.Model):
    """
    Semantic grouping for SchemaColumnTemplates.

    Categories are:
    - Global
    - Stable (identified by `identifier`)
    - Used for UI organization only
    """

    identifier = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Stable system identifier (e.g. 'valuation', 'cash_flow').",
    )

    name = models.CharField(
        max_length=100,
        help_text="Human-readable category name (e.g. 'Valuation').",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description for UI/tooltips.",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Controls ordering in UI lists.",
    )

    is_system = models.BooleanField(
        default=False,
        help_text="System categories cannot be deleted or renamed.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def clean(self):
        super().clean()
        if self.pk:
            previous = SchemaColumnCategory.objects.filter(pk=self.pk).first()
            if previous and previous.is_system:
                if self.identifier != previous.identifier:
                    raise ValidationError(
                        "System category identifier cannot be changed."
                    )
                if self.name != previous.name:
                    raise ValidationError(
                        "System category name cannot be changed."
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System categories cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
