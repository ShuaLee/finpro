from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from schemas.validators import validate_constraints



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
        return f"{self.name}"

    def clean(self):
        super().clean()
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if (
                self.content_type_id != original.content_type_id or
                self.object_id != original.object_id
            ):
                raise ValidationError(
                    "Schema portfolio assignment cannot be changed once saved.")


class SchemaColumn(models.Model):
    """
    Represents a column in a schema.
    Columns define attributes for holdings/accounts and can be:
    - asset-based,
    - holding-based,
    - calculated (via formula/template),
    - custom.
    """

    schema = models.ForeignKey(
        "schemas.Schema",
        on_delete=models.CASCADE,
        related_name="columns"
    )
    template = models.ForeignKey(
        "schemas.SchemaColumnTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this column was created from, if any"
    )
    formula = models.ForeignKey(
        "formulas.Formula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Direct formula if this is a custom calculated column"
    )

    title = models.CharField(max_length=100)

    identifier = models.SlugField(
        max_length=100,
        blank=False,
        null=False,
        help_text="Stable internal key used for referencing this column in formulas. Auto-generated for custom columns.",
    )

    data_type = models.CharField(max_length=20, choices=[
        ("decimal", "Number"),
        ("string", "Text"),
        ("date", "Date"),
        ("datetime", "Datetime"),
        ("time", "Time"),
        ("url", "URL"),
    ])
    source = models.CharField(max_length=20, choices=[
        ("asset", "Asset"),
        ("holding", "Holding"),
        ("calculated", "Calculated"),
        ("custom", "Custom"),
    ])
    source_field = models.CharField(max_length=100, blank=True, null=True)

    is_editable = models.BooleanField(default=True)
    is_deletable = models.BooleanField(default=True)
    is_system = models.BooleanField(
        default=False, help_text="Whether this is a system default column"
    )

    constraints = models.JSONField(default=dict, blank=True)

    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.source})"
    
    def clean(self):
        super().clean()

        if not self.identifier:
            raise ValidationError("SchemaColumn.identifier must be set explicitly (use SchemaGenerator).")
        


class SchemaColumnValue(models.Model):
    """
    Represents a value for a specific column in an account or holding.
    Uses GenericForeignKey for flexible linking.
    """
    column = models.ForeignKey(
        SchemaColumn, on_delete=models.CASCADE, related_name='values')

    account_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    account_id = models.PositiveIntegerField()
    account = GenericForeignKey('account_ct', 'account_id')

    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    def get_value(self):
        """
        Return the stored SCV value.
        Always correct because the manager syncs it with source or edit.
        """
        return self.value

    

    class Meta:
        unique_together = ('column', 'account_ct', 'account_id')

    def __str__(self):
        return f"{self.account} - {self.column.title}: {self.value}"
    
    def save(self, *args, **kwargs):
        from schemas.services.schema_column_value_manager import SchemaColumnValueManager
        manager = SchemaColumnValueManager(self)
        manager.apply_rules()  # ensures rounding/constraints are applied
        super().save(*args, **kwargs)  # persist cleaned value




# class CustomAssetSchemaConfig(models.Model):
#     """
#     Stores custom schema configurations for user-defined asset types.
#     """
#     asset_type = models.CharField(max_length=100, unique=True)
#     config = models.JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "Asset Schema Config"
#         verbose_name_plural = "Asset Schema Configs"

#     def __str__(self):
#         return f"SchemaConfig: {self.asset_type}"
