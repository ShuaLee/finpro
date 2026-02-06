from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect

from accounts.models.holding import Holding

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
from schemas.services.schema_column_edit_service import SchemaColumnEditService
from schemas.services.schema_column_value_edit_service import SchemaColumnValueEditService
from schemas.services.schema_column_value_manager import SchemaColumnValueManager
from schemas.services.schema_constraint_edit_service import SchemaConstraintEditService
from schemas.services.schema_constraint_enum_resolver import SchemaConstraintEnumResolver


from decimal import Decimal


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

        if scv.column.data_type == "boolean":
            self.fields["value"].widget = forms.CheckboxInput()

    def clean_value(self):
        value = self.cleaned_data.get("value")
        scv = self.instance
        column = scv.column

        # Allow clearing value (used for revert logic)
        if value in ("", None):
            return None

        # ---------------- ENUM ----------------
        enum_constraint = column.constraints.filter(name="enum").first()
        if enum_constraint:
            allowed = SchemaConstraintEnumResolver.resolve(
                enum_constraint,
                column=column,
                holding=scv.holding,
            )
            if value not in allowed:
                raise forms.ValidationError(
                    f"Value must be one of: {', '.join(allowed)}"
                )

        # ---------------- TYPE VALIDATION ----------------
        try:
            if column.data_type == "decimal":
                Decimal(str(value))
            elif column.data_type == "integer":
                int(value)
            elif column.data_type == "boolean":
                if not isinstance(value, bool):
                    raise ValueError()
            else:
                str(value)
        except Exception:
            raise forms.ValidationError(
                f"Invalid value for type '{column.data_type}'."
            )

        # ---------------- CONSTRAINT VALIDATION ----------------
        for constraint in column.constraints.all():
            try:
                constraint.validate(value)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)

        return value


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

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        # ----------------------------------
        # Load PREVIOUS state
        # ----------------------------------
        previous = SchemaColumn.objects.get(pk=obj.pk)

        # Save the column (admin already mutated obj)
        super().save_model(request, obj, form, change)

        # ----------------------------------
        # Detect changed fields
        # ----------------------------------
        changed_fields = [
            field
            for field in form.changed_data
        ]

        # ----------------------------------
        # Delegate to service
        # ----------------------------------
        SchemaColumnEditService.update_column(
            column=obj,
            changed_fields=changed_fields,
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
        "display_value",  # ✅ formatted value
        "source",
    )

    form = SchemaColumnValueAdminForm
    change_form_template = "admin/schemas/schemacolumnvalue/change_form.html"

    # ----------------------------
    # Display
    # ----------------------------
    def display_value(self, obj):
        return SchemaColumnValueManager(obj).get_display_value()

    display_value.short_description = "Value"

    # ----------------------------
    # Read-only logic
    # ----------------------------
    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ("column", "holding", "source")

        holding = obj.holding

        is_custom_asset = (
            holding is not None
            and holding.source == Holding.SOURCE_CUSTOM
        )

        # Custom holdings: ALWAYS editable
        if is_custom_asset:
            return ("column", "holding", "source")

        # Market-backed holdings: respect column editability
        if obj.column.is_editable:
            return ("column", "holding", "source")

        return ("column", "holding", "source", "value")

    # ----------------------------
    # Save handling
    # ----------------------------

    def save_model(self, request, obj, form, change):
        if not change:
            super().save_model(request, obj, form, change)
            return

        try:
            SchemaColumnValueEditService.set_value(
                scv=obj,
                raw_value=form.cleaned_data["value"],
            )
        except ValidationError as e:
            # Properly surface service-level errors in admin
            self.message_user(
                request,
                e.messages[0],
                level=messages.ERROR,
            )
            return

    # ----------------------------
    # Revert button handler
    # ----------------------------

    def response_change(self, request, obj):
        if "_revert_to_system" in request.POST:
            if obj.source == SchemaColumnValue.Source.USER:
                SchemaColumnValueEditService.revert(scv=obj)
                self.message_user(request, "Reverted to system value.")
            else:
                self.message_user(
                    request,
                    "This value is already using the system source.",
                    level="info",
                )

            return HttpResponseRedirect(request.path)

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

    def save_model(self, request, obj, form, change):
        if not change:
            obj.save()
            return

        SchemaConstraintEditService.update_constraint(
            constraint=obj,
            user=request.user,
            changed_fields=form.changed_data,
            updates=form.cleaned_data,
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
