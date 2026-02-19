from django.db import models
from django.core.exceptions import ValidationError

from schemas.models.schema import Schema
from schemas.models.schema_column_template import SchemaColumnTemplate


class SchemaColumn(models.Model):
    """
    Concrete column inside a schema.
    """

    schema = models.ForeignKey(
        Schema,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    identifier = models.SlugField(max_length=100)
    title = models.CharField(max_length=255)

    data_type = models.CharField(
        max_length=20,
        choices=SchemaColumnTemplate._meta.get_field("data_type").choices,
    )

    template = models.ForeignKey(
        SchemaColumnTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="schema_columns",
        help_text="Null = user-created column",
    )

    is_system = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("schema", "identifier")
        ordering = ["display_order", "id"]

    def clean(self):
        super().clean()
        if self.is_system and self.is_deletable:
            raise ValidationError("System columns cannot be deletable.")
        if self.data_type not in {
            "decimal",
            "percent",
            "string",
            "boolean",
            "date",
        }:
            raise ValidationError("Unsupported schema column data_type.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from schemas.policies.schema_column_deletion_policy import SchemaColumnDeletionPolicy
        SchemaColumnDeletionPolicy.assert_deletable(column=self)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.identifier} ({self.schema_id})"

    def behavior_for(self, asset_type):
        """
        Return the SchemaColumnAssetBehavior for this asset type,
        or None if undefined.
        """
        return self.asset_behaviors.filter(
            asset_type=asset_type
        ).first()
