from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from schemas.validators import validate_value_against_constraints
import re


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
    field_path = models.CharField(blank=True, null=True, max_length=255)

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

    @property
    def display_title(self):
        return self.title

    @property
    def effective_formula(self):
        if self.template and self.template.formula:
            return self.template.formula
        return self.formula

    def clean(self):
        super().clean()

        # Normalize "number" -> "decimal"
        if self.data_type == "number":
            self.data_type = "decimal"

        # Title cannot be blank
        if not self.title:
            raise ValidationError("Column title cannot be blank.")

        # Enforce source_field for asset/holding
        if self.source in ["asset", "holding"] and not self.source_field:
            raise ValidationError(
                f"source_field is required for source='{self.source}'."
            )

        # --- Enforce snake_case on ALL source_fields ---
        if self.source_field:
            if not re.match(r'^[a-z][a-z0-9_]*$', self.source_field):
                raise ValidationError(
                    "source_field must be snake_case (e.g. 'purchase_price')."
                )

        # --- Custom column rules ---
        if self.source == "custom" and not self.pk and not self.schema_id:
            self.is_system = False
            self.is_deletable = True

            if self.data_type not in ("string", "decimal"):
                raise ValidationError(
                    "Custom columns must be of type 'string' or 'decimal'."
                )

            if self.data_type == "decimal":
                dp = self.constraints.get("decimal_places")
                if dp is None:
                    self.constraints["decimal_places"] = 2
                elif not (0 <= int(dp) <= 8):
                    raise ValidationError(
                        "decimal_places must be between 0 and 8."
                    )

            if not self.source_field:
                # Generate a snake_case field name
                self.source_field = re.sub(r'[^a-z0-9_]', '_',
                                           (self.title or "").lower()) or "custom_field"

            if self.template:
                raise ValidationError(
                    "Custom columns cannot link to a template."
                )

        # --- Enforce immutability on system columns ---
        if self.pk:
            original = type(self).objects.only(
                "schema_id", "data_type", "source", "source_field", "field_path", "is_system"
            ).get(pk=self.pk)

            if self.schema_id != original.schema_id:
                raise ValidationError(
                    "Schema assignment cannot be changed after creation."
                )

            if self.is_system or original.is_system:
                locked_fields = ["data_type", "source",
                                 "source_field", "field_path"]
                errors = {}
                for field in locked_fields:
                    if getattr(self, field) != getattr(original, field):
                        errors[field] = f"'{field}' is locked because this is a system column."
                if errors:
                    raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()

        # Auto-assign display order
        if self._state.adding and self.display_order == 0:
            max_order = (
                SchemaColumn.objects.filter(schema=self.schema)
                .aggregate(models.Max("display_order"))["display_order__max"]
            )
            self.display_order = (max_order or 0) + 1

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Prevent deleting this column if other columns in the same schema
        depend on its `source_field`.
        """
        if not self.source_field:
            return super().delete(*args, **kwargs)

        dependents = []

        # 1. Custom calculated columns (direct formula FK)
        custom_dependents = SchemaColumn.objects.filter(
            schema=self.schema,
            formula__dependencies__contains=[self.source_field]
        ).exclude(id=self.id)

        dependents.extend(list(custom_dependents))

        # 2. Template-driven calculated columns (formula lives on template)
        template_dependents = SchemaColumn.objects.filter(
            schema=self.schema,
            template__formula__dependencies__contains=[self.source_field]
        ).exclude(id=self.id)

        dependents.extend(list(template_dependents))

        if dependents:
            titles = ", ".join([d.title for d in dependents])
            raise ValidationError(
                f"❌ Cannot delete column '{self.title}' because it is required by: {titles}"
            )

        return super().delete(*args, **kwargs)


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

    class Meta:
        unique_together = ('column', 'account_ct', 'account_id')

    def __str__(self):
        return f"{self.account} - {self.column.title}: {self.value}"

    def get_value(self):
        return self.value

    def clean(self):
        constraints = self.column.constraints or {}
        data_type = self.column.data_type
        validate_value_against_constraints(self.value, data_type, constraints)


class CustomAssetSchemaConfig(models.Model):
    """
    Stores custom schema configurations for user-defined asset types.
    """
    asset_type = models.CharField(max_length=100, unique=True)
    config = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Asset Schema Config"
        verbose_name_plural = "Asset Schema Configs"

    def __str__(self):
        return f"SchemaConfig: {self.asset_type}"
