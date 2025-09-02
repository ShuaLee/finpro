from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.text import slugify

from formulas.models import Formula

from schemas.models import Schema
from schemas.services.schema_column_adder import SchemaColumnAdder
from schemas.services.schema_deletion import delete_schema_if_allowed
from schemas.admin.add_forms import AddFromTemplateForm, AddCustomColumnForm, AddCalculatedColumnForm


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "schema_type", "created_at")
    list_filter = ("schema_type",)
    search_fields = ["name"]
    readonly_fields = ("schema_type", "content_type",
                       "object_id", "created_at")
    fields = ("name", "schema_type", "content_type", "object_id", "created_at")

    actions = ["delete_selected_safely"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        try:
            delete_schema_if_allowed(obj)
            obj.delete()
            self.message_user(
                request, f"✅ Deleted schema: {obj}", level=messages.SUCCESS
            )
        except ValidationError as e:
            self.message_user(
                request,
                f"❌ Could not delete schema '{obj}': {'; '.join(e.messages)}",
                level=messages.ERROR,
            )

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
                    f"❌ Could not delete schema '{schema}': {'; '.join(e.messages)}"
                )

        if deleted:
            self.message_user(
                request, f"✅ Deleted {deleted} schemas successfully.", level=messages.SUCCESS
            )

        for msg in failed:
            self.message_user(request, msg, level=messages.ERROR)

    # --- Custom admin URLs ---
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:schema_id>/add-from-template/",
                self.admin_site.admin_view(self.add_from_template),
                name="schema_add_from_template",
            ),
            path(
                "<int:schema_id>/add-custom/",
                self.admin_site.admin_view(self.add_custom_column),
                name="schema_add_custom",
            ),
            path(
                "<int:schema_id>/add-calculated/",
                self.admin_site.admin_view(self.add_calculated_column),
                name="schema_add_calculated",
            ),
        ]
        return custom + urls

    # --- Add column from template ---
    def add_from_template(self, request, schema_id):
        schema = get_object_or_404(Schema, pk=schema_id)
        if request.method == "POST":
            form = AddFromTemplateForm(schema, request.POST)
            if form.is_valid():
                template = form.cleaned_data["template"]
                try:
                    column, created = SchemaColumnAdder(
                        schema).add_from_template(template)
                    if created:
                        messages.success(
                            request, f"✅ Added new column: {column.title}")
                    else:
                        messages.warning(
                            request, f"⚠️ Column '{column.title}' already exists in this schema.")
                except ValidationError as e:
                    messages.error(request, f"❌ {e.messages[0]}")
                return redirect("admin:schemas_schema_change", schema.id)
        else:
            form = AddFromTemplateForm(schema)
        return render(request, "admin/schemas/add_from_template.html", {"form": form, "schema": schema})

    # --- Add custom column ---

    def add_custom_column(self, request, schema_id):
        schema = get_object_or_404(Schema, pk=schema_id)
        if request.method == "POST":
            form = AddCustomColumnForm(request.POST)
            if form.is_valid():
                SchemaColumnAdder(schema).add_custom_column(
                    title=form.cleaned_data["title"],
                    data_type=form.cleaned_data["data_type"],
                    constraints=(
                        {"decimal_places": int(
                            form.cleaned_data["decimal_places"])}
                        if form.cleaned_data["data_type"] == "decimal"
                        else {}
                    ),
                )
                messages.success(
                    request, f"✅ Added custom column: {form.cleaned_data['title']}"
                )
                return redirect("admin:schemas_schema_change", schema.id)
        else:
            form = AddCustomColumnForm()
        return render(
            request,
            "admin/schemas/add_custom_column.html",
            {"form": form, "schema": schema},
        )
    
    def add_calculated_column(self, request, schema_id):
        schema = get_object_or_404(Schema, pk=schema_id)
        if request.method == "POST":
            form = AddCalculatedColumnForm(schema, request.POST)
            if form.is_valid():
                title = form.cleaned_data["title"]
                expression = form.cleaned_data["expression"]

                # Extract identifiers from the expression (simple regex for a-z, underscores)
                import re
                identifiers = set(re.findall(r"[a-z_][a-z0-9_]*", expression))

                # Create formula
                formula = Formula.objects.create(
                    key=slugify(title),
                    title=title,
                    expression=expression,
                    dependencies=list(identifiers),
                    decimal_places=2,
                    is_system=False,
                    created_by=request.user,
                )

                # Create SchemaColumn linked to formula
                schema.columns.create(
                    title=title,
                    data_type="decimal",
                    source="calculated",
                    formula=formula,
                    is_editable=False,
                    is_deletable=True,
                    is_system=False,
                )

                messages.success(request, f"✅ Added calculated column: {title}")
                return redirect("admin:schemas_schema_change", schema.id)
        else:
            form = AddCalculatedColumnForm(schema)

        return render(
            request,
            "admin/schemas/add_calculated_column.html",
            {"form": form, "schema": schema},
        )

    # --- Inject buttons into Schema detail page ---
    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["add_from_template_url"] = reverse(
            "admin:schema_add_from_template", args=[object_id]
        )
        extra_context["add_custom_url"] = reverse(
            "admin:schema_add_custom", args=[object_id]
        )
        extra_context["add_calculated_url"] = reverse("admin:schema_add_calculated", args=[object_id])
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )
