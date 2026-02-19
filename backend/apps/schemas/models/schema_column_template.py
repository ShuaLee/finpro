from django.db import models
from django.core.exceptions import ValidationError

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
            ("decimal", "Number"),
            ("percent", "Percent"),
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

    def clean(self):
        super().clean()
        if self.pk:
            previous = SchemaColumnTemplate.objects.filter(pk=self.pk).first()
            if previous and previous.is_system:
                immutable_fields = ("identifier", "data_type", "is_system")
                for field in immutable_fields:
                    if getattr(self, field) != getattr(previous, field):
                        raise ValidationError(
                            f"System template field '{field}' cannot be changed."
                        )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_system:
            raise ValidationError("System templates cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.identifier
