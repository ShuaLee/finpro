from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    SchemaColumnTemplate,
    SchemaColumnVisibility,
    SubPortfolioSchemaLink,
    CustomAssetSchemaConfig,
)
from schemas.services.schema_deletion import delete_schema_if_allowed

# Inlines


class SchemaColumnInline(admin.TabularInline):  # or StackedInline
    model = SchemaColumn
    extra = 0
    fields = ("title", "data_type", "field_path", "is_default", "is_system")
    readonly_fields = ("created_at",)


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "get_user_email",
                    "get_portfolio_type", "created_at")
    list_filter = ("schema_type", "content_type")
    search_fields = ["name"]
    readonly_fields = ["created_at"]

    actions = ["delete_selected_safely"]

    inlines = [SchemaColumnInline]

    def get_user_email(self, obj):
        try:
            return obj.content_object.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"

    def get_portfolio_type(self, obj):
        try:
            return obj.content_object.__class__.__name__
        except AttributeError:
            return "-"
    get_portfolio_type.short_description = "Subportfolio Type"

    def delete_model(self, request, obj):
        """
        Prevent deletion if it's the last schema for a portfolio/account type.
        """
        try:
            delete_schema_if_allowed(obj)
            obj.delete()
            self.message_user(
                request, f"✅ Deleted schema: {obj}", level=messages.SUCCESS)
        except ValidationError as e:
            self.message_user(
                request, f"❌ Could not delete schema '{obj}': {e.messages[0]}", level=messages.ERROR)

    @admin.action(description="Delete selected schemas with validation")
    def delete_selected_safely(self, request, queryset):
        deleted = 0
        failed = []

        for schema in queryset:
            try:
                delete_schema_if_allowed(schema)
                schema.delete()
                deleted += 1
            except ValidationError as e:
                failed.append(
                    f"❌ Could not delete schema '{schema}': {e.messages[0]}")

        if deleted:
            self.message_user(
                request, f"✅ Deleted {deleted} schemas successfully.", level=messages.SUCCESS)

        for error in failed:
            self.message_user(request, error, level=messages.ERROR)

    @admin.action(description="Delete orphaned schemas (no subportfolio link)")
    def delete_orphaned_schemas(self, request, queryset):
        from schemas.models import SubPortfolioSchemaLink

        orphaned = queryset.exclude(
            id__in=SubPortfolioSchemaLink.objects.values_list(
                "schema_id", flat=True)
        )

        count = orphaned.count()
        for schema in orphaned:
            schema.delete()

        self.message_user(request, f"✅ Deleted {count} orphaned schemas.")


@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "schema", "source",
                    "data_type", "display_order", "is_system")
    list_filter = ("source", "data_type", "is_system")
    search_fields = ("title", "schema__name")
    autocomplete_fields = ["schema"]
    readonly_fields = ("created_at",)


@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = ["get_account_model_name", "title",
                    "source", "source_field", "data_type", "is_default"]
    list_filter = ["source", "is_default", "is_system"]
    search_fields = ["title", "source_field"]
    ordering = ["display_order"]
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "source", "source_field",
                "data_type", "field_path",
                "editable", "is_default", "is_deletable", "is_system",
                "formula_method", "formula_expression",
                "constraints",
                "display_order", "investment_theme", "created_at"
            )
        }),
    )

    @admin.display(description="Account Model")
    def get_account_model_name(self, obj):
        return obj.account_model_ct.model_class().__name__ if obj.account_model_ct else "-"


@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "holding", "value")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)
    list_filter = ("column__schema",)


@admin.register(SchemaColumnVisibility)
class SchemaColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = ("id", "column", "account", "is_visible")
    list_filter = ("is_visible", "column__schema")
    search_fields = ("column__title",)
    autocomplete_fields = ("column",)


@admin.register(SubPortfolioSchemaLink)
class SubPortfolioSchemaLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "subportfolio", "account_model", "schema")
    list_filter = ("schema__schema_type",)
    autocomplete_fields = ("schema",)
    search_fields = ("subportfolio_id", "account_model_id")


@admin.register(CustomAssetSchemaConfig)
class CustomAssetSchemaConfigAdmin(admin.ModelAdmin):
    list_display = ['asset_type', 'created_at', 'updated_at']
    search_fields = ['asset_type']
