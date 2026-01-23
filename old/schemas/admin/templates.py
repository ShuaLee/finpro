from django.contrib import admin
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn


class SchemaTemplateColumnInline(admin.TabularInline):
    model = SchemaTemplateColumn
    extra = 0
    ordering = ["display_order", "id"]
    fields = (
        "title", "identifier", "data_type", "source", "source_field",
        "formula", "is_system", "is_default", "display_order",
    )
    autocomplete_fields = ["formula"]
    show_change_link = True


@admin.register(SchemaTemplate)
class SchemaTemplateAdmin(admin.ModelAdmin):
    list_display = ("account_type", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "account_type__name")
    inlines = [SchemaTemplateColumnInline]


@admin.register(SchemaTemplateColumn)
class SchemaTemplateColumnAdmin(admin.ModelAdmin):
    list_display = (
        "title", "identifier", "template", "data_type", "source", "display_order",
    )
    list_filter = ("template__account_type", "data_type", "source")
    search_fields = ("title", "identifier", "template__name")
    autocomplete_fields = ["formula"]
