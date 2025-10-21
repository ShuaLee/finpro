from django.contrib import admin
from schemas.models.schema import Schema, SchemaColumn, SchemaColumnValue


# -------------------------------------------------------------------
# Inline Admins
# -------------------------------------------------------------------

class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    extra = 0
    readonly_fields = (
        "identifier",
        "title",
        "data_type",
        "source",
        "source_field",
        "is_editable",
        "is_system",
        "display_order",
    )
    can_delete = False


class SchemaColumnValueInline(admin.TabularInline):
    model = SchemaColumnValue
    extra = 0
    readonly_fields = ("column", "holding", "value", "is_edited")
    can_delete = False


# -------------------------------------------------------------------
# Main Schema Admin
# -------------------------------------------------------------------

@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    """Admin view for inspecting schemas per portfolio/account type."""
    list_display = (
        "id",
        "get_name",
        "portfolio",
        "account_type",
        "created_at",
    )
    list_filter = ("account_type", "portfolio")
    search_fields = ("portfolio__name", "portfolio__profile__user__email")
    ordering = ("portfolio", "account_type")

    readonly_fields = ("portfolio", "account_type", "created_at", "updated_at")

    inlines = [SchemaColumnInline]

    def get_name(self, obj):
        """Fallback if 'name' is not a DB field."""
        return getattr(obj, "name", f"Schema for {obj.account_type}")
    get_name.short_description = "Name"


# -------------------------------------------------------------------
# SchemaColumn Admin
# -------------------------------------------------------------------

@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    """Manage or inspect individual schema columns."""
    list_display = (
        "id",
        "schema",
        "title",
        "identifier",
        "data_type",
        "source",
        "source_field",
        "is_editable",
        "is_system",
        "display_order",
    )
    list_filter = ("data_type", "is_system", "is_editable")
    search_fields = ("title", "identifier", "source_field")
    ordering = ("schema", "display_order")
    readonly_fields = ("identifier", "schema")


# -------------------------------------------------------------------
# SchemaColumnValue Admin
# -------------------------------------------------------------------

@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    """View all column values per holding."""
    list_display = (
        "id",
        "holding",
        "column",
        "value",
        "is_edited",
    )
    list_filter = ("is_edited",)
    search_fields = (
        "holding__asset__name",
        "holding__asset__identifiers__value",
        "column__title",
    )
    ordering = ("column", "holding")
    readonly_fields = ("holding", "column", "value", "is_edited")
