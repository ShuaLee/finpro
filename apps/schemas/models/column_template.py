from django.db import models
from django.utils.text import slugify


class SchemaColumnTemplate(models.Model):
    """
    Template definition for SchemaColumns used in schema initialization.
    One per (asset_type, source_field).
    """
    asset_type = models.CharField(max_length=50)
    source = models.CharField(max_length=20, choices=[
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ])
    source_field = models.CharField(max_length=100, blank=True, null=True)

    title = models.CharField(max_length=100)
    data_type = models.CharField(max_length=20, choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('time', 'Time'),
        ('url', 'URL'),
    ])
    field_path = models.CharField(max_length=255, null=True, blank=True)
    editable = models.BooleanField(default=True)
    is_default = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)

    formula_expression = models.TextField(null=True, blank=True)
    formula_method = models.CharField(max_length=100, null=True, blank=True)
    constraints = models.JSONField(default=dict, blank=True)

    investment_theme = models.ForeignKey(
        'assets.InvestmentTheme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If this column represents a custom theme, link it here."
    )

    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Schema Column Template"
        verbose_name_plural = "Schema Column Templates"
        unique_together = ("asset_type", "source", "source_field")
        ordering = ["display_order"]

    def __str__(self):
        return f"[{self.asset_type}] {self.title} ({self.source})"

    def clean(self):
        if not self.title:
            raise ValueError("Template must have a title.")

        if self.source in ["asset", "holding"] and not self.source_field:
            raise ValueError(
                f"source_field required for source '{self.source}'")

        if self.source == "custom":
            if self.data_type not in ("decimal", "string"):
                raise ValueError("Custom columns must be decimal or string.")
            if self.data_type == "decimal" and self.decimal_places is None:
                raise ValueError("Decimal places required for decimal type.")
            if not self.source_field:
                self.source_field = slugify(self.title)

        # Ensure only one formula type is set
        if self.formula_expression and self.formula_method:
            raise ValueError(
                "Only one of formula_expression or formula_method can be set.")
