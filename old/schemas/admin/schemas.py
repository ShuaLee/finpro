from django.contrib import admin
from schemas.models.schema import Schema, SchemaColumn, SchemaColumnValue


class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    extra = 0
    ordering = ["display_order", "id"]
    fields = (
        "title", "identifier", "data_type", "source", "source_field",
        "formula", "is_system", "is_deletable", "display_order",
    )
    autocomplete_fields = ["formula"]
    show_change_link = True


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "account_type", "created_at")
    list_filter = ("account_type",)
    search_fields = ("portfolio__profile__user__email",)
    inlines = [SchemaColumnInline]


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        "title", "identifier", "schema", "data_type",
        "source", "is_system", "display_order",
    )
    list_filter = ("schema__account_type", "data_type", "source")
    search_fields = ("title", "identifier",
                     "schema__portfolio__profile__user__email")
    autocomplete_fields = ["formula"]


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("holding", "column", "value", "source", "updated_at")
    list_filter = ("source", "column__schema__account_type")
    search_fields = ("holding__account__name", "column__title")
