from django.db import models


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

    is_system = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["identifier"]

    def __str__(self):
        return self.identifier
