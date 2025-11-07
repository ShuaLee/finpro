from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path, reverse

from schemas.models.schema import Schema, SchemaColumn, SchemaColumnValue
from schemas.models.template import SchemaTemplateColumn
from schemas.services.schema_column_factory import SchemaColumnFactory


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
    list_display = ("id", "get_name", "portfolio",
                    "account_type", "created_at")
    list_filter = ("account_type", "portfolio")
    search_fields = ("portfolio__name", "portfolio__profile__user__email")
    ordering = ("portfolio", "account_type")
    readonly_fields = ("portfolio", "account_type", "created_at", "updated_at")
    inlines = [SchemaColumnInline]

    def get_name(self, obj):
        return getattr(obj, "name", f"Schema for {obj.account_type}")
    get_name.short_description = "Name"

    # ------------------------------------------------------------
    # Custom admin buttons
    # ------------------------------------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:schema_id>/add-from-template/",
                self.admin_site.admin_view(self.add_from_template_view),
                name="schemas_schema_add_from_template",
            ),
            path(
                "<int:schema_id>/add-custom-column/",
                self.admin_site.admin_view(self.add_custom_column_view),
                name="schemas_schema_add_custom_column",
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        schema = Schema.objects.get(pk=object_id)
        extra_context["add_from_template_url"] = reverse(
            "admin:schemas_schema_add_from_template", args=[schema.id]
        )
        extra_context["add_custom_column_url"] = reverse(
            "admin:schemas_schema_add_custom_column", args=[schema.id]
        )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    # ------------------------------------------------------------
    # 1️⃣ Add from Template View
    # ------------------------------------------------------------
    def add_from_template_view(self, request, schema_id):
        schema = get_object_or_404(Schema, id=schema_id)

        available_columns = SchemaTemplateColumn.objects.filter(
            template__account_type=schema.account_type
        ).order_by("display_order", "title")

        if request.method == "POST":
            template_col_id = request.POST.get("template_column")
            try:
                column = SchemaColumnFactory.add_from_template(
                    schema, template_col_id)
                messages.success(
                    request, f"Added column '{column.title}' from template successfully."
                )
                return redirect("admin:schemas_schema_change", schema.id)
            except Exception as e:
                messages.error(request, f"Error adding column: {e}")

        context = {
            "opts": self.model._meta,
            "schema": schema,
            "available_columns": available_columns,
            "title": f"Add Column from Template to {schema}",
        }
        return render(request, "admin/schemas/add_from_template.html", context)

    # ------------------------------------------------------------
    # 2️⃣ Add Custom Column View
    # ------------------------------------------------------------
    class CustomColumnForm(forms.Form):
        title = forms.CharField(max_length=255, label="Column Title")
        data_type = forms.ChoiceField(
            choices=[
                ("string", "String"),
                ("decimal", "Decimal"),
                ("integer", "Integer"),
                ("date", "Date"),
                ("boolean", "Boolean"),
                ("url", "URL"),
            ],
            label="Data Type",
        )

    def add_custom_column_view(self, request, schema_id):
        schema = get_object_or_404(Schema, id=schema_id)

        if request.method == "POST":
            form = self.CustomColumnForm(request.POST)
            if form.is_valid():
                try:
                    column = SchemaColumnFactory.add_custom_column(
                        schema=schema,
                        title=form.cleaned_data["title"],
                        data_type=form.cleaned_data["data_type"],
                    )
                    messages.success(
                        request, f"Custom column '{column.title}' added successfully."
                    )
                    return redirect("admin:schemas_schema_change", schema.id)
                except Exception as e:
                    messages.error(request, f"Error: {e}")
        else:
            form = self.CustomColumnForm()

        context = {
            "opts": self.model._meta,
            "schema": schema,
            "form": form,
            "title": f"Add Custom Column to {schema}",
        }
        return render(request, "admin/schemas/add_custom_column.html", context)

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

    def delete_queryset(self, request, queryset):
        from schemas.services.schema_column_factory import SchemaColumnFactory
        deleted_count = 0
        for column in queryset:
            SchemaColumnFactory.delete_column(column)
            deleted_count += 1
        if deleted_count:
            self.message_user(
                request, f"Deleted {deleted_count} column(s) and resequenced.", level=messages.SUCCESS)


# -------------------------------------------------------------------
# SchemaColumnValue Admin
# -------------------------------------------------------------------

@admin.register(SchemaColumnValue)
class SchemaColumnValueAdmin(admin.ModelAdmin):
    """View all column values per holding."""
    list_display = ("id", "holding", "column", "value", "is_edited")
    list_filter = ("is_edited",)
    search_fields = (
        "holding__asset__name",
        "holding__asset__identifiers__value",
        "column__title",
    )
    ordering = ("column", "holding")
    readonly_fields = ("holding", "column", "value", "is_edited")
