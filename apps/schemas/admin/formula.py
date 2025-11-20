from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms

from schemas.models.formula import Formula
from schemas.models.schema import Schema, SchemaColumn
from schemas.services.formulas.resolver import FormulaDependencyResolver
from schemas.services.formulas.builder import FormulaBuilder
from schemas.services.formulas.column_updater import FormulaColumnUpdater


# ================================================================
# FORM — Extra validation BEFORE save
# ================================================================

class FormulaAdminForm(forms.ModelForm):
    class Meta:
        model = Formula
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()

        expr = cleaned.get("expression")
        formula = self.instance

        if not expr:
            raise ValidationError("Formula expression cannot be empty.")

        # Parse identifiers
        resolver = FormulaDependencyResolver(formula)
        try:
            deps = resolver.extract_identifiers()
        except Exception as e:
            raise ValidationError(f"Invalid formula expression: {e}")

        if not deps:
            raise ValidationError(
                "Formula must reference at least one identifier (e.g., price, quantity)."
            )

        # Schema-scoped: ensure schema present
        if not formula.is_system and not formula.schema:
            raise ValidationError(
                "Custom formulas must be associated with a schema."
            )

        return cleaned


# ================================================================
# Inline showing which SchemaColumns use this formula
# ================================================================

class SchemaColumnInline(admin.TabularInline):
    model = SchemaColumn
    fk_name = "formula"
    extra = 0
    readonly_fields = ("title", "identifier", "schema", "data_type")
    can_delete = False
    verbose_name = "Column using this formula"
    verbose_name_plural = "Columns using this formula"

    fields = (
        "title",
        "identifier",
        "schema",
        "data_type",
    )


# ================================================================
# ADMIN
# ================================================================

@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    """
    Formula admin:
        ✔ Validate expression
        ✔ Show dependencies
        ✔ Attach formula to schema columns
        ✔ Prevent editing system formulas except by dev
    """

    form = FormulaAdminForm
    inlines = [SchemaColumnInline]

    list_display = (
        "title",
        "key",
        "schema",
        "is_system",
        "created_at",
    )

    list_filter = ("is_system", "schema")
    search_fields = ("title", "key", "expression")

    readonly_fields = (
        "created_at",
        "updated_at",
        "dependencies_display",
        "attach_to_column_action",
    )

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "key",
                "description",
                "expression",
                "dependencies_display",
            )
        }),
        ("Precision", {
            "fields": ("decimal_places",)
        }),
        ("Scope", {
            "fields": ("schema", "is_system")
        }),
        ("Attach Formula", {
            "fields": ("attach_to_column_action",),
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at")
        }),
    )

    # ============================================================
    # Display parsed dependencies
    # ============================================================
    def dependencies_display(self, obj):
        if not obj.pk:
            return "Save formula to view dependencies."

        try:
            deps = FormulaDependencyResolver(obj).extract_identifiers()
        except Exception as e:
            return f"❌ Error parsing: {e}"

        if not deps:
            return "⚠ No dependencies detected"

        return ", ".join(deps)

    dependencies_display.short_description = "Dependencies (identifiers used)"

    # ============================================================
    # Action field for attaching formula to a SchemaColumn
    # ============================================================
    def attach_to_column_action(self, obj):
        if not obj.pk:
            return "Save formula to enable attachment."

        # Build a dynamic list of schema columns
        schema = obj.schema

        if obj.is_system:
            return "System formulas are not attached here."

        if not schema:
            return "Assign formula to a schema to enable attachment."

        html = []
        for col in schema.columns.filter(source__in=("holding", "asset", "custom")):
            url = f"/admin/schemas/schemacolumn/{col.id}/change/?attach_formula={obj.id}"
            html.append(f"<a href='{url}'>{col.title}</a>")

        return "<br>".join(html) if html else "No attachable columns."

    attach_to_column_action.allow_tags = True
    attach_to_column_action.short_description = "Attach formula to column"

    # ============================================================
    # Prevent editing system formulas
    # ============================================================
    def has_change_permission(self, request, obj=None):
        if obj and obj.is_system and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)
