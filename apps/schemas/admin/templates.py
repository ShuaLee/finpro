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
