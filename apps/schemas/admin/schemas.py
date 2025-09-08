from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from schemas.models import Schema, SchemaColumn, SchemaColumnValue
from schemas.validators import validate_constraints
from decimal import Decimal


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type",
                    "subportfolio", "account_type", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "created_at")


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "schema",
        "source",
        "source_field",
        "data_type",
        "identifier",
        "is_editable",
        "is_system",
        "display_order",
        "created_at",
    )
    search_fields = ("title", "identifier", "source_field")
    list_filter = ("schema", "source", "data_type", "is_system", "is_editable")
    ordering = ("schema", "display_order")


class SchemaColumnValueForm(forms.ModelForm):
    class Meta:
        model = SchemaColumnValue
        fields = "__all__"

    def clean_value(self):
        value = self.cleaned_data.get("value")
        column = self.instance.column

        if value in [None, ""]:
            return value

        dt = column.data_type
        try:
            if dt == "decimal":
                value = Decimal(str(value))
            elif dt == "integer":
                value = int(value)
            elif dt == "string":
                value = str(value)
        except Exception:
            raise ValidationError(f"'{value}' is not a valid {dt}")

        # Apply constraints (min/max/choices etc.)
        try:
            validate_constraints(dt, column.constraints)
        except Exception as e:
            raise ValidationError(str(e))

        return value


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    form = SchemaColumnValueForm
    list_display = (
        "id",
        "column",
        "holding",
        "value",
        "is_edited",
    )
    search_fields = (
        "column__title",
        "holding__asset__symbol",
        "holding__account__name",
        "value",
    )
    list_filter = ("is_edited", "column__schema")
    raw_id_fields = ("column", "holding")  # ✅ both real FKs
