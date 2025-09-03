from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
import re


class SchemaColumnTemplate(models.Model):
    """
    Template definition for SchemaColumns used in schema initialization.
    One per (account_model, schema_type, source_field).
    """

    account_model_ct = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="The account model this template applies to."
    )

    schema_type = models.CharField(max_length=50)

    # Link to a formula if this template defines a calculated column
    formula = models.ForeignKey(
        "formulas.Formula",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text="If this is a calculated column, link to the formula"
    )

    source = models.CharField(max_length=20, choices=[
        ("asset", "Asset"),
        ("holding", "Holding"),
        ("calculated", "Calculated"),
        ("custom", "Custom"),
    ])

    # ✅ snake_case stable key, not a slug
    source_field = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stable identifier in snake_case, e.g. 'price', 'purchase_price', 'unrealized_gain'"
    )

    title = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=[
        ("decimal", "Number"),
        ("string", "Text"),
        ("date", "Date"),
        ("datetime", "Datetime"),
        ("time", "Time"),
        ("url", "URL"),
    ])

    # Behavior flags
    is_editable = models.BooleanField(default=True)
    is_default = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)

    constraints = models.JSONField(default=dict, blank=True)

    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("account_model_ct", "schema_type", "source_field")
        ordering = ["display_order"]

    def __str__(self):
        model = self.account_model_ct.model_class()
        model_name = model.__name__ if model else "Unknown"
        return f"[{model_name}] {self.title} ({self.source_field})"

    def clean(self):
        if not self.title:
            raise ValidationError("Template must have a title.")

        if self.source in ["asset", "holding"] and not self.source_field:
            raise ValidationError(f"source_field required for source '{self.source}'")

        if self.source == "custom":
            if self.data_type not in ("decimal", "string"):
                raise ValidationError("Custom columns must be decimal or string.")
            if self.data_type == "decimal" and "decimal_places" not in self.constraints:
                raise ValidationError("decimal_places required for decimal columns.")

        # ✅ enforce snake_case for source_field
        if self.source_field:
            if not re.match(r'^[a-z][a-z0-9_]*$', self.source_field):
                raise ValidationError("source_field must be snake_case (e.g. 'purchase_price').")

    def save(self, *args, **kwargs):
        self.full_clean()  # ensures validation is run
        super().save(*args, **kwargs)