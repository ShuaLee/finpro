from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms

from schemas.models.formula import Formula
from schemas.services.formulas.resolver import FormulaDependencyResolver


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

        resolver = FormulaDependencyResolver(formula)
        try:
            deps = resolver.extract_identifiers()
        except Exception as e:
            raise ValidationError(f"Invalid formula expression: {e}")

        if not isinstance(deps, list):
            raise ValidationError("Dependencies must resolve to a list.")

        return cleaned


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):

    form = FormulaAdminForm

    list_display = (
        "title",
        "identifier",
        "is_system",
        "created_at",
    )

    list_filter = ("is_system",)
    search_fields = ("title", "identifier", "expression")

    readonly_fields = (
        "created_at",
        "updated_at",
        "dependencies_display",
        "attached_columns_display",
    )

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "identifier",
                "description",
                "expression",
                "dependencies_display",
            )
        }),
        ("Precision", {
            "fields": ("decimal_places",)
        }),
        ("System metadata", {
            "fields": ("is_system",)
        }),
        ("Attached Columns", {
            "fields": ("attached_columns_display",),
        }),
        ("Meta", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def dependencies_display(self, obj):
        if not obj.pk:
            return "Save first to see dependencies."

        try:
            deps = FormulaDependencyResolver(obj).extract_identifiers()
            return ", ".join(deps) if deps else "(none)"
        except Exception as e:
            return f"Error parsing: {e}"

    dependencies_display.short_description = "Dependencies"

    def attached_columns_display(self, obj):
        """Show SchemaColumns using this formula."""
        cols = obj.schema_columns.all()
        if not cols:
            return "No SchemaColumns attached."

        html = []
        for col in cols:
            url = f"/admin/schemas/schemacolumn/{col.id}/change/"
            html.append(f"<a href='{url}'>{col.title}</a>")

        return "<br>".join(html)

    attached_columns_display.allow_tags = True
    attached_columns_display.short_description = "Attached Schema Columns"
