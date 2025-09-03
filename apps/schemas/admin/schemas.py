from django.contrib import admin
from schemas.models import Schema, SchemaColumn, SchemaColumnValue


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "portfolio", "created_at")
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


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "column",
        "account",
        "value",
        "is_edited",
    )
    search_fields = ("column__title", "account_id", "value")
    list_filter = ("is_edited", "column__schema")
    raw_id_fields = ("column", "account_ct")  # keeps admin light