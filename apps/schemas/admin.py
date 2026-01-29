from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect

from schemas.models import (
    Schema,
    SchemaColumn,
    SchemaColumnValue,
    MasterConstraint,
    SchemaConstraint,
)
from schemas.models.account_column_visibility import AccountColumnVisibility
from schemas.models.schema_column_template import SchemaColumnTemplate
from schemas.models.schema_column_template_behaviour import SchemaColumnTemplateBehaviour
from schemas.models.schema_column_asset_behaviour import SchemaColumnAssetBehaviour
from schemas.services.schema_column_dependency_graph import SchemaColumnDependencyGraph
from schemas.services.schema_column_value_edit_service import SchemaColumnValueEditService
from schemas.services.schema_constraint_enum_resolver import SchemaConstraintEnumResolver

from django import forms


class SchemaColumnValueAdminForm(forms.ModelForm):
    class Meta:
        model = SchemaColumnValue
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        scv = self.instance
        if not scv.pk:
            return

        enum_constraint = scv.column.constraints.filter(name="enum").first()
        if not enum_constraint:
            return

        choices = SchemaConstraintEnumResolver.resolve(
            enum_constraint,
            column=scv.column,
            holding=scv.holding,
        )

        self.fields["value"].widget = forms.Select(
            choices=[(c, c) for c in choices]
        )


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

    def dependency_graph(self, request, schema_id):
        schema = Schema.objects.get(id=schema_id)

        dot = SchemaColumnDependencyGraph.as_dot(schema=schema)

        return HttpResponse(
            dot,
            content_type="text/plain",
        )

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()

        custom = [
            path(
                "dependency-graph/<int:schema_id>/",
                self.admin_site.admin_view(self.dependency_graph),
                name="schema_dependency_graph",
            ),
        ]

        return custom + urls


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

    def delete_model(self, request, obj):
        from schemas.services.schema_column_factory import SchemaColumnFactory

        SchemaColumnFactory.delete_column(obj)

    def delete_queryset(self, request, queryset):
        from schemas.services.schema_column_factory import SchemaColumnFactory

        for column in queryset:
            SchemaColumnFactory.delete_column(column)

    def has_delete_permission(self, request, obj=None):
        if obj and not obj.is_deletable:
            return False
        return super().has_delete_permission(request, obj)


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

    form = SchemaColumnValueAdminForm

    # 👇 IMPORTANT
    change_form_template = (
        "admin/schemas/schemacolumnvalue/change_form.html"
    )

    # --------------------------------------------------
    # Readonly logic
    # --------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ("column", "holding", "source")

        enum_constraint = obj.column.constraints.filter(name="enum").exists()

        if enum_constraint and obj.source != SchemaColumnValue.Source.FORMULA:
            # allow editing value only
            return ("column", "holding", "source")

        return ("column", "holding", "source", "value")

    # --------------------------------------------------
    # Save handling
    # --------------------------------------------------
    def save_model(self, request, obj, form, change):
        if change:
            SchemaColumnValueEditService.update_value(
                scv=obj,
                raw_value=form.cleaned_data["value"],
            )
        else:
            super().save_model(request, obj, form, change)

    # --------------------------------------------------
    # Handle "Revert to system" button
    # --------------------------------------------------
    def response_change(self, request, obj):
        if "_revert_to_system" in request.POST:
            SchemaColumnValueEditService.revert_to_system(scv=obj)
            self.message_user(request, "Reverted to system value.")
            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

    # --------------------------------------------------
    # Inject template context flag
    # --------------------------------------------------
    def render_change_form(self, request, context, *args, **kwargs):
        context["show_revert_button"] = True
        return super().render_change_form(request, context, *args, **kwargs)

    # --------------------------------------------------
    # Permissions
    # --------------------------------------------------
    def has_delete_permission(self, request, obj=None):
        return True


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


@admin.register(AccountColumnVisibility)
class AccountColumnVisibilityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "column",
        "is_visible",
    )

    list_filter = (
        "is_visible",
        "account__account_type",
    )

    search_fields = (
        "account__name",
        "column__identifier",
        "column__title",
    )

    list_editable = ("is_visible",)

    ordering = ("account", "column__display_order")
