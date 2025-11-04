from django.contrib import admin
from schemas.models.template import SchemaTemplate, SchemaTemplateColumn


class SchemaTemplateColumnInline(admin.TabularInline):
    model = SchemaTemplateColumn
    extra = 0
    fields = (
        "title",
        "identifier",
        "data_type",
        "source",
        "source_field",
        "is_editable",
        "is_deletable",
        "is_system",
        "display_order",
    )


@admin.register(SchemaTemplate)
class SchemaTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "account_type", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "account_type")
    inlines = [SchemaTemplateColumnInline]


@admin.register(SchemaTemplateColumn)
class SchemaTemplateColumnAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "identifier",
        "template",
        "data_type",
        "source",
        "is_default",
        "is_system",
        "is_editable",
        "display_order",
    )
    list_filter = ("data_type", "source", "is_default",
                   "is_system", "is_editable")
    search_fields = ("title", "identifier", "template__name", "source_field")
    ordering = ("template", "display_order", "title")
    autocomplete_fields = ("template",)

    fieldsets = (
        (None, {
            "fields": (
                "template",
                "title",
                "identifier",
                "data_type",
                "source",
                "source_field",
            )
        }),
        ("Display & Behavior", {
            "fields": (
                "is_default",
                "is_editable",
                "is_deletable",
                "is_system",
                "display_order",
            ),
        }),
    )
