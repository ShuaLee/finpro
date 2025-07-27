from django.contrib import admin
from schemas.models.core import Schema, SchemaColumn, SchemaColumnValue


class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    extra = 1
    fields = ("title", "data_type", "source", "source_field",
              "editable", "is_deletable", "formula")
    readonly_fields = ("source",)


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "portfolio", "created_at")
    search_fields = ("name", "schema_type")
    inlines = [SchemaColumnInline]


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "schema", "data_type",
                    "source", "editable", "is_deletable")
    list_filter = ("data_type", "source", "schema__schema_type")
    search_fields = ("title", "schema__name")


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "value", "is_edited")
    search_fields = ("column__title",)
    list_filter = ("is_edited",)
