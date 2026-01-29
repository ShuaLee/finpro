from django.db import models

from schemas.models.schema_column_category import SchemaColumnCategory


class SchemaColumnTemplate(models.Model):
    """
    System-defined semantic column blueprint.
    Immutable.
    """

    identifier = models.SlugField(
        max_length=100,
        help_text="Semantic identifier (e.g. current_value, quantity).",
        unique=True,
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    data_type = models.CharField(
        max_length=20,
        choices=[
            ("decimal", "Decimal"),
            ("integer", "Integer"),
            ("string", "String"),
            ("boolean", "Boolean"),
            ("date", "Date"),
        ],
    )

    category = models.ForeignKey(
        SchemaColumnCategory,
        on_delete=models.PROTECT,
        related_name="templates",
        null=True,
        blank=True,
        help_text="Semantic category used for UI grouping.",
    )

    constraint_overrides = models.JSONField(
        null=True,
        blank=True,
        help_text="Constraint overrides applied when this template is expanded into a schema column."
    )

    is_system = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return self.identifier
