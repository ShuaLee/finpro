from django.contrib import admin
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnVisibility
)
from django.contrib.contenttypes.admin import GenericTabularInline


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "schema_type", "content_type", "object_id", "created_at")
    search_fields = ("name", "schema_type")
    list_filter = ("schema_type", "content_type")
    readonly_fields = ("created_at",)


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        "title", "schema", "data_type", "source",
        "source_field", "editable", "is_deletable", "created_at"
    )
    list_filter = ("schema", "source", "data_type", "editable")
    search_fields = ("title", "source_field", "schema__name")
    readonly_fields = ("created_at",)


class SchemaColumnValueInline(GenericTabularInline):
    model = SchemaColumnValue
    extra = 0
    fields = ("column", "value", "is_edited")
    readonly_fields = ("is_edited",)
    autocomplete_fields = ("column",)


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("column", "account", "value", "is_edited")
    list_filter = ("column__schema", "is_edited")
    search_fields = ("column__title", "account__name")
    autocomplete_fields = ("column",)


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
