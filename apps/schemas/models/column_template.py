from django.db import models
from django.core.exceptions import ValidationError
import re


class SchemaColumnTemplate(models.Model):
    """
    Template definition for SchemaColumns used in schema initialization.
    One per (account_type, source_field).
    """

    account_type = models.CharField(
        max_length=50,
        help_text="AccountType this template applies to (e.g., stock_self, crypto_wallet)."
    )

    # Link to a formula if this template defines a calculated column
    formula = models.ForeignKey(
        "formulas.Formula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If this is a calculated column, link to the formula"
    )

    source = models.CharField(max_length=20, choices=[
        ("asset", "Asset"),
        ("holding", "Holding"),
        ("calculated", "Calculated"),
        ("custom", "Custom"),
    ])

    source_field = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stable identifier in snake_case, e.g. 'price', 'purchase_price'"
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

    is_editable = models.BooleanField(default=True)
    is_default = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)

    constraints = models.JSONField(default=dict, blank=True)

    display_order = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("account_type", "source_field", "source")
        ordering = ["display_order"]

    def __str__(self):
        return f"[{self.account_type}] {self.title} ({self.source_field})"

    def clean(self):
        if not self.title:
            raise ValidationError("Template must have a title.")

        if self.source in ["asset", "holding"] and not self.source_field:
            raise ValidationError(
                f"source_field required for source '{self.source}'"
            )

        if self.source == "custom":
            if self.data_type not in ("decimal", "string"):
                raise ValidationError(
                    "Custom columns must be decimal or string."
                )
            if self.data_type == "decimal" and "decimal_places" not in self.constraints:
                raise ValidationError(
                    "decimal_places required for decimal columns."
                )

        if self.source_field:
            if not re.match(r'^[a-z][a-z0-9_]*$', self.source_field):
                raise ValidationError(
                    "source_field must be snake_case (e.g. 'purchase_price')."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
