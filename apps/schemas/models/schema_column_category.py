from django.db import models


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

    def __str__(self) -> str:
        return self.name
