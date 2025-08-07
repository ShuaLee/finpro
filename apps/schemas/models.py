from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError


class Schema(models.Model):
    """
    Represents a dynamic schema linked to any sub-portfolio (Stock, Metal, Custom).
    Each schema defines the structure of holdings/accounts under that sub-portfolio.
    """
    name = models.CharField(max_length=100)
    schema_type = models.CharField(max_length=50)  # e.g., stock, metal, custom

    # Generic link to sub-portfolio
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    portfolio = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.schema_type.capitalize()} Schema: {self.name}"


class SchemaColumn(models.Model):
    """
    Represents a column in a schema.
    Columns define attributes for holdings/accounts and can be asset-based, holding-based, calculated, or custom.
    """
    schema = models.ForeignKey(
        Schema, on_delete=models.CASCADE, related_name="columns")
    title = models.CharField(max_length=100)
    custom_title = models.CharField(max_length=100, blank=True, null=True)

    data_type = models.CharField(max_length=20, choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('time', 'Time'),
        ('url', 'URL'),
    ])
    source = models.CharField(max_length=20, choices=[
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ])
    source_field = models.CharField(max_length=100, blank=True, null=True)
    field_path = models.CharField(blank=True, null=True, max_length=255)
    editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    decimal_places = models.PositiveSmallIntegerField(null=True, blank=True)
    is_system = models.BooleanField(
        default=False, help_text="Whether this is a system default column")
    scope = models.CharField(max_length=20, choices=[
        ('portfolio', 'Portfolio-wide'),
        ('subportfolio', 'Subportfolio-wide'),
        ('account', 'Account-specific')
    ], default='subportfolio')
    formula_method = models.CharField(
        max_length=100, blank=True, null=True, help_text="Backend Python method to evaluate this column")
    formula_expression = models.TextField(
        null=True,
        blank=True,
        help_text="User-defined formula like '(quantity * price) / pe_ratio' -> something that wont be in the backend."
    )
    display_order = models.PositiveIntegerField(default=0)

    # This field does not mean that each SchemaColumn maps to one theme across all holdings. Instead, it's a soft link
    investment_theme = models.ForeignKey(
        'assets.InvestmentTheme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If this column represents a custom theme, link it here."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.source})"

    @property
    def display_title(self):
        return self.custom_title or self.title

    def clean(self):
        # 🧠 Ensure only one of the formula types is set
        formula_fields = [
            bool(self.formula_method and self.formula_method.strip()),
            bool(self.formula_expression and self.formula_expression.strip()),
        ]
        if sum(formula_fields) > 1:
            raise ValidationError(
                "Only one of formula, formula_method, or formula_expression can be set.")

        # 🔔 Ensure title is not blank
        if not self.title:
            raise ValidationError("Column title cannot be blank.")

        # 🔍 Warn if field_path is missing for asset/holding sources
        if self.source in ["asset", "holding"] and not self.source_field:
            raise ValidationError(
                f"source_field is required for source='{self.source}'.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self._state.adding and self.display_order == 0:
            max_order = (
                SchemaColumn.objects.filter(schema=self.schema).aggregate(
                    models.Max("display_order"))["display_order__max"]
            )
            self.display_order = (max_order or 0) + 1
        super().save(*args, **kwargs)


class SchemaColumnValue(models.Model):
    """
    Represents a value for a specific column in an account or holding.
    Uses GenericForeignKey for flexible linking.
    """
    column = models.ForeignKey(
        SchemaColumn, on_delete=models.CASCADE, related_name='values')

    # Generic reference to Account or Holding
    account_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    account_id = models.PositiveIntegerField()
    account = GenericForeignKey('account_ct', 'account_id')

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ('column', 'account_ct', 'account_id')

    def __str__(self):
        return f"{self.account} - {self.column.title}: {self.value}"

    def get_value(self):
        return self.value


class SchemaColumnVisibility(models.Model):
    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="visibility_settings"
    )

    # Generic relation to any account model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey()

    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "content_type", "object_id")

    def __str__(self):
        return f"{self.account} | {self.column.title}: {'Visible' if self.is_visible else 'Hidden'}"


"""
Custom asset config.
"""


class CustomAssetSchemaConfig(models.Model):
    """
    Stores custom schema configurations for user-defined asset types.
    """
    asset_type = models.CharField(max_length=100, unique=True)
    config = models.JSONField()  # Holds schema definition
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Schema Config"
        verbose_name_plural = "Asset Schema Configs"

    def __str__(self):
        return f"SchemaConfig: {self.asset_type}"
