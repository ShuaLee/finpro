from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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

    data_type = models.CharField(max_length=20, choices=[
        ('decimal', 'Decimal'),
        ('integer', 'Integer'),
        ('string', 'Text'),
        ('date', 'Date'),
        ('url', 'URL'),
    ])
    source = models.CharField(max_length=20, choices=[
        ('asset', 'Asset'),
        ('holding', 'Holding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ])
    source_field = models.CharField(max_length=100, blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
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

    formula_expression = models.TextField(
        null=True,
        blank=True,
        help_text="User-defined formula like '(quantity * price) / pe_ratio' -> something that wont be in the backend."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.source})"


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
