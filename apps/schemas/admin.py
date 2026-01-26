from django.contrib import admin

from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    MasterConstraint,
    SchemaConstraint,
)
from schemas.models.template import SchemaTemplate
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import SchemaColumnTemplateBehaviour
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour


# ============================================================
# SCHEMA TEMPLATES
# ============================================================

@admin.register(SchemaTemplate)
class SchemaTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_type",
        "is_base",
        "is_active",
    )
    list_filter = (
        "is_base",
        "is_active",
        "account_type",
    )
    search_fields = ("name",)
    ordering = ("account_type__slug", "name")


# ============================================================
# COLUMN TEMPLATES (GLOBAL CATALOG)
# ============================================================

@admin.register(SchemaColumnTemplate)
class SchemaColumnTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "title",
        "data_type",
        "is_system",
    )
    list_filter = (
        "data_type",
        "is_system",
    )
    search_fields = ("identifier", "title")
    ordering = ("identifier",)

    readonly_fields = (
        "identifier",
        "is_system",
    )

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


# ============================================================
# TEMPLATE BEHAVIOURS (DEFAULT EXECUTION PER ASSET TYPE)
# ============================================================

@admin.register(SchemaColumnTemplateBehaviour)
class SchemaColumnTemplateBehaviourAdmin(admin.ModelAdmin):
    list_display = (
        "template",
        "asset_type",
        "source",
        "formula_definition",
    )
    list_filter = (
        "asset_type",
        "source",
    )
    search_fields = (
        "template__identifier",
        "formula_definition__identifier",
    )


# ============================================================
# LIVE SCHEMAS
# ============================================================

@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "portfolio",
        "account_type",
    )
    list_filter = ("account_type",)
    search_fields = ("portfolio__profile__user__email",)


# ============================================================
# LIVE SCHEMA COLUMNS (STRUCTURE ONLY)
# ============================================================

@admin.register(SchemaColumn)
class SchemaColumnAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "schema",
        "data_type",
        "is_system",
        "is_editable",
        "is_deletable",
    )
    list_filter = (
        "data_type",
        "is_system",
    )
    search_fields = ("identifier",)
    ordering = ("schema", "display_order")

    readonly_fields = (
        "identifier",
        "schema",
        "is_system",
    )


# ============================================================
# PER-ASSET COLUMN BEHAVIOURS (LIVE OVERRIDES)
# ============================================================

@admin.register(SchemaColumnAssetBehaviour)
class SchemaColumnAssetBehaviourAdmin(admin.ModelAdmin):
    list_display = (
        "column",
        "asset_type",
        "source",
        "formula_definition",
        "is_override",
    )
    list_filter = (
        "asset_type",
        "source",
        "is_override",
    )
    search_fields = (
        "column__identifier",
        "formula_definition__identifier",
    )


# ============================================================
# SCHEMA COLUMN VALUES
# ============================================================

@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    list_display = (
        "column",
        "holding",
        "value",
        "source",
    )
    list_filter = ("source",)
    search_fields = (
        "column__identifier",
        "holding__asset__name",
    )


# ============================================================
# CONSTRAINTS
# ============================================================

@admin.register(MasterConstraint)
class MasterConstraintAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "label",
        "applies_to",
    )
    list_filter = ("applies_to",)
    search_fields = ("name", "label")


@admin.register(SchemaConstraint)
class SchemaConstraintAdmin(admin.ModelAdmin):
    list_display = (
        "column",
        "name",
        "applies_to",
        "is_editable",
    )
    list_filter = (
        "applies_to",
        "is_editable",
    )
    search_fields = (
        "column__identifier",
        "name",
    )
