from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from schemas.validators import validate_value_against_constraints
from decimal import Decimal, InvalidOperation
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

    identifier = models.SlugField(
        max_length=100,
        blank=True,
        null=True,
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
        
        if not self.identifier:
            base = re.sub(r'[^a-z0-9_]', '_', (self.title or "").lower())
            base = re.sub(r'_+', '_', base).strip('_') or "col"
            proposed = base
            counter = 1

            while SchemaColumn.objects.filter(
                schema=self.schema,
                identifier=proposed
            ).exclude(pk=self.pk).exists():
                counter += 1
                proposed = f"{base}_{counter}"

            self.identifier = proposed

        # --- Auto-generate + ensure uniqueness of source_field for custom ---
        if self.source == "custom" and not self.pk:
            if not self.identifier:
                # Create slug-style identifier
                base = re.sub(r'[^a-z0-9_]', '_', self.title.lower())
                base = re.sub(r'_+', '_', base).strip('_') or "custom_field"
                proposed = base
                counter = 1

                while SchemaColumn.objects.filter(
                    schema=self.schema,
                    identifier=proposed
                ).exclude(pk=self.pk).exists():
                    counter += 1
                    proposed = f"{base}_{counter}"

                self.identifier = proposed

            if self.template:
                raise ValidationError("Custom columns cannot link to a template.")

            self.is_system = False
            self.is_deletable = True

            if self.data_type not in ("string", "decimal"):
                raise ValidationError("Custom columns must be of type 'string' or 'decimal'.")

            if self.data_type == "decimal":
                dp = self.constraints.get("decimal_places")
                if dp is None:
                    self.constraints["decimal_places"] = 2
                elif not (0 <= int(dp) <= 8):
                    raise ValidationError("decimal_places must be between 0 and 8.")

        # --- Enforce snake_case on ALL source_fields ---
        if self.source_field:
            if not re.match(r'^[a-z][a-z0-9_]*$', self.source_field):
                raise ValidationError("source_field must be snake_case (e.g. 'purchase_price').")

        # --- Enforce immutability on system columns ---
        if self.pk:
            original = type(self).objects.only(
                "schema_id", "data_type", "source", "source_field", "field_path", "is_system"
            ).get(pk=self.pk)

            if self.schema_id != original.schema_id:
                raise ValidationError("Schema assignment cannot be changed after creation.")

            if self.is_system or original.is_system:
                locked_fields = ["data_type", "source", "source_field", "field_path"]
                errors = {
                    field: f"'{field}' is locked because this is a system column."
                    for field in locked_fields
                    if getattr(self, field) != getattr(original, field)
                }
                if errors:
                    raise ValidationError(errors)

        # 🔒 Final safety: check uniqueness of source_field per schema
        if self.source_field and self.schema_id:
            conflict_qs = SchemaColumn.objects.filter(
                schema_id=self.schema_id,
                source_field=self.source_field
            )
            if self.pk:
                conflict_qs = conflict_qs.exclude(pk=self.pk)
            if conflict_qs.exists():
                raise ValidationError({
                    "source_field": f"A column with source_field='{self.source_field}' already exists in this schema."
                })


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
        if self.is_edited:
            return self._cast_runtime(self.value)

        if self.column.source_field or self.column.field_path:
            return self._resolve_source_value()

        return self._default_value()
    
    def _cast_runtime(self, value):
        dt = self.column.data_type
        if value in [None, ""]:
            return None
        if dt == "decimal":
            return Decimal(str(value))
        if dt == "integer":
            return int(value)
        return value

    def clean(self):
        if not self.is_edited:
            return  # ✅ Skip validation if value is not manually edited

        constraints = self.column.constraints or {}
        data_type = self.column.data_type
        validate_value_against_constraints(self.value, data_type, constraints)

    def _resolve_source_value(self):
        value = None

        if self.column.field_path:
            value = self._resolve_field_path(self.column.field_path)
        elif self.column.source_field:
            value = getattr(self.account, self.column.source_field, None)

        # If value is still None, apply default fallback
        if value is None:
            if self.column.data_type == "decimal":
                dp = int(self.column.constraints.get("decimal_places", 2))
                return Decimal("0").quantize(Decimal(f"1.{'0'*dp}"))
            elif self.column.data_type == "string":
                return "-"
            # You can add more fallbacks here as needed

        return value
    
    def _resolve_field_path(self, path: str):
        """Utility to walk dotted field paths (like 'stock.price')."""
        value = self.account
        for part in path.split("."):
            value = getattr(value, part, None)
            if value is None:
                break
        return value
    
    def _cast_value(self, value):
        data_type = self.column.data_type

        if value in [None, ""]:
            return None

        try:
            if data_type == "decimal":
                return str(Decimal(str(value)))  # Store as string, casted
            elif data_type == "string":
                return str(value)
            elif data_type == "integer":
                return str(int(value))
            # Add more types as needed
        except Exception:
            return value  # Let clean() catch bad data

        return value
    
    def save(self, *args, **kwargs):
        if self.is_edited:
            self.value = self._cast_and_stringify(self.value)
        else:
            resolved = self._resolve_source_value()
            if resolved is not None:
                self.value = resolved

        super().save(*args, **kwargs)
        self.recompute_dependents()


    def _cast_and_stringify(self, value):
        """
        Casts the edited value to the correct type, validates it,
        and returns it as a string (because SCV.value is TextField).
        """
        data_type = self.column.data_type

        if value in [None, ""]:
            return None

        try:
            if data_type == "decimal":
                # ⚠️ Cast to Decimal, then save as string
                return str(Decimal(str(value)))

            elif data_type == "integer":
                return str(int(value))

            elif data_type in ["string", "url"]:
                return str(value)

            # Extend as needed

        except (InvalidOperation, ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for type {data_type}: {value} ({e})")

        return str(value)  # fallback

    def recompute_dependents(self):
        """
        Recompute all calculated columns in the same schema
        that depend on this column.identifier.
        """
        from schemas.services.schema_engine import HoldingSchemaEngine  # 🔑 lazy import here

        schema = self.column.schema
        dependents = schema.columns.filter(source="calculated")

        for col in dependents:
            formula = col.effective_formula
            if not formula:
                continue
            if self.column.identifier in (formula.dependencies or []):
                engine = HoldingSchemaEngine(self.account, schema.schema_type)
                engine.sync_column(col)
    



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
