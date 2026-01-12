# from django import forms
# from django.contrib import admin, messages
# from django.db import models
# from django.forms import TextInput
# from django.shortcuts import redirect, render, get_object_or_404
# from django.urls import path, reverse

# from schemas.models.schema import Schema, SchemaColumn, SchemaColumnValue
# from schemas.models.template import SchemaTemplateColumn
# from schemas.services.schema_column_factory import SchemaColumnFactory


# # -------------------------------------------------------------------
# # Inline Admins
# # -------------------------------------------------------------------

# class SchemaColumnInline(admin.TabularInline):
#     model = SchemaColumn
#     extra = 0
#     readonly_fields = (
#         "identifier",
#         "title",
#         "data_type",
#         "source",
#         "source_field",
#         "is_editable",
#         "is_system",
#         "display_order",
#     )
#     can_delete = False


# class SchemaColumnValueInline(admin.TabularInline):
#     model = SchemaColumnValue
#     extra = 0
#     readonly_fields = ("column", "holding", "value", "is_edited")
#     can_delete = False


# # -------------------------------------------------------------------
# # Main Schema Admin
# # -------------------------------------------------------------------


# @admin.register(Schema)
# class SchemaAdmin(admin.ModelAdmin):
#     """Admin view for inspecting schemas per portfolio/account type."""
#     list_display = ("id", "get_name", "portfolio",
#                     "account_type", "created_at")
#     list_filter = ("account_type", "portfolio")
#     search_fields = ("portfolio__name", "portfolio__profile__user__email")
#     ordering = ("portfolio", "account_type")
#     readonly_fields = ("portfolio", "account_type", "created_at", "updated_at")
#     inlines = [SchemaColumnInline]

#     def get_name(self, obj):
#         return getattr(obj, "name", f"Schema for {obj.account_type}")
#     get_name.short_description = "Name"

#     # ------------------------------------------------------------
#     # Custom admin buttons
#     # ------------------------------------------------------------
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path(
#                 "<int:schema_id>/add-from-template/",
#                 self.admin_site.admin_view(self.add_from_template_view),
#                 name="schemas_schema_add_from_template",
#             ),
#             path(
#                 "<int:schema_id>/add-custom-column/",
#                 self.admin_site.admin_view(self.add_custom_column_view),
#                 name="schemas_schema_add_custom_column",
#             ),
#         ]
#         return custom_urls + urls

#     def change_view(self, request, object_id, form_url="", extra_context=None):
#         extra_context = extra_context or {}
#         schema = Schema.objects.get(pk=object_id)
#         extra_context["add_from_template_url"] = reverse(
#             "admin:schemas_schema_add_from_template", args=[schema.id]
#         )
#         extra_context["add_custom_column_url"] = reverse(
#             "admin:schemas_schema_add_custom_column", args=[schema.id]
#         )
#         return super().change_view(request, object_id, form_url, extra_context=extra_context)

#     # ------------------------------------------------------------
#     # 1️⃣ Add from Template View
#     # ------------------------------------------------------------
#     def add_from_template_view(self, request, schema_id):
#         schema = get_object_or_404(Schema, id=schema_id)

#         available_columns = SchemaTemplateColumn.objects.filter(
#             template__account_type=schema.account_type
#         ).order_by("display_order", "title")

#         if request.method == "POST":
#             template_col_id = request.POST.get("template_column")
#             try:
#                 column = SchemaColumnFactory.add_from_template(
#                     schema, template_col_id)
#                 messages.success(
#                     request, f"Added column '{column.title}' from template successfully."
#                 )
#                 return redirect("admin:schemas_schema_change", schema.id)
#             except Exception as e:
#                 messages.error(request, f"Error adding column: {e}")

#         context = {
#             "opts": self.model._meta,
#             "schema": schema,
#             "available_columns": available_columns,
#             "title": f"Add Column from Template to {schema}",
#         }
#         return render(request, "admin/schemas/add_from_template.html", context)

#     # ------------------------------------------------------------
#     # 2️⃣ Add Custom Column View
#     # ------------------------------------------------------------
#     class CustomColumnForm(forms.Form):
#         title = forms.CharField(max_length=255, label="Column Title")
#         data_type = forms.ChoiceField(
#             choices=[
#                 ("string", "String"),
#                 ("decimal", "Decimal"),
#                 ("integer", "Integer"),
#                 ("date", "Date"),
#                 ("boolean", "Boolean"),
#                 ("url", "URL"),
#             ],
#             label="Data Type",
#         )

#     def add_custom_column_view(self, request, schema_id):
#         schema = get_object_or_404(Schema, id=schema_id)

#         if request.method == "POST":
#             form = self.CustomColumnForm(request.POST)
#             if form.is_valid():
#                 try:
#                     column = SchemaColumnFactory.add_custom_column(
#                         schema=schema,
#                         title=form.cleaned_data["title"],
#                         data_type=form.cleaned_data["data_type"],
#                     )
#                     messages.success(
#                         request, f"Custom column '{column.title}' added successfully."
#                     )
#                     return redirect("admin:schemas_schema_change", schema.id)
#                 except Exception as e:
#                     messages.error(request, f"Error: {e}")
#         else:
#             form = self.CustomColumnForm()

#         context = {
#             "opts": self.model._meta,
#             "schema": schema,
#             "form": form,
#             "title": f"Add Custom Column to {schema}",
#         }
#         return render(request, "admin/schemas/add_custom_column.html", context)

# # -------------------------------------------------------------------
# # SchemaColumn Admin
# # -------------------------------------------------------------------


# @admin.register(SchemaColumn)
# class SchemaColumnAdmin(admin.ModelAdmin):
#     """Manage or inspect individual schema columns."""
#     list_display = (
#         "id",
#         "schema",
#         "title",
#         "identifier",
#         "data_type",
#         "source",
#         "source_field",
#         "is_editable",
#         "is_system",
#         "display_order",
#     )
#     list_filter = ("data_type", "is_system", "is_editable")
#     search_fields = ("title", "identifier", "source_field")
#     ordering = ("schema", "display_order")
#     readonly_fields = ("identifier", "schema")

#     def delete_queryset(self, request, queryset):
#         """
#         Override bulk delete to use the factory for consistency.
#         Resequence only once per schema after all deletions.
#         """
#         from schemas.services.schema_column_factory import SchemaColumnFactory
#         from schemas.services.schema_manager import SchemaManager

#         # Track affected schemas
#         affected_schemas = set()

#         for column in queryset:
#             try:
#                 schema = column.schema
#                 affected_schemas.add(schema.id)
#                 SchemaColumnFactory.delete_column(column)
#             except Exception as e:
#                 self.message_user(
#                     request,
#                     f"Error deleting column '{column.title}': {e}",
#                     level=messages.ERROR,
#                 )

#         # ✅ Resequence each affected schema *once*
#         for schema_id in affected_schemas:
#             from schemas.models.schema import Schema
#             schema = Schema.objects.get(id=schema_id)
#             SchemaManager(schema).resequence_for_schema(schema)

#         self.message_user(
#             request,
#             f"Successfully deleted {queryset.count()} column(s) and resequenced affected schemas.",
#             level=messages.SUCCESS,
#         )


# # -------------------------------------------------------------------
# # SchemaColumnValue Admin
# # -------------------------------------------------------------------

# @admin.register(SchemaColumnValue)
# class SchemaColumnValueAdmin(admin.ModelAdmin):

#     class SCVForm(forms.ModelForm):
#         class Meta:
#             model = SchemaColumnValue
#             fields = ["holding", "column", "value", "is_edited"]
#             widgets = {
#                 "value": TextInput(attrs={"size": 40}),
#             }

#     form = SCVForm

#     list_display = ("id", "holding", "column", "value", "is_edited")
#     list_filter = ("is_edited", "column__is_editable")
#     ordering = ("holding", "column")
#     fields = ("holding", "column", "value", "is_edited")

#     # Ensure Django doesn't freeze the field early
#     def get_form(self, request, obj=None, **kwargs):
#         kwargs["form"] = self.form
#         return super().get_form(request, obj, **kwargs)

#     # ------------------------------
#     # READONLY LOGIC (fixed)
#     # ------------------------------
#     def get_readonly_fields(self, request, obj=None):

#         # NEW SCV creation should never happen in admin → readonly
#         if obj is None:
#             return ("holding", "column", "value", "is_edited")

#         col = obj.column

#         # 1️⃣ Formula columns → always readonly
#         if col.source == "formula":
#             return ("holding", "column", "value", "is_edited")

#         # 2️⃣ Explicitly non-editable columns → readonly
#         if not col.is_editable:
#             return ("holding", "column", "value", "is_edited")

#         # 3️⃣ Editable holding-sourced columns → value is editable
#         if col.source == "holding":
#             return ("holding", "column")

#         # 4️⃣ Editable asset-sourced columns → value is editable
#         if col.source == "asset":
#             return ("holding", "column")

#         # 5️⃣ Custom editable columns → value is editable
#         if col.source == "custom":
#             return ("holding", "column")

#         # Fallback: fully readonly
#         return ("holding", "column", "value", "is_edited")

#     # ------------------------------
#     # SAVE MODEL OVERRIDE (critical)
#     # ------------------------------
#     def save_model(self, request, obj, form, change):
#         """
#         Delegate saving to SCV Manager and ensure admin
#         correctly sends is_edited True/False based on checkbox.
#         """
#         from schemas.services.schema_column_value_manager import SchemaColumnValueManager

#         manager = SchemaColumnValueManager(obj)

#         new_value = form.cleaned_data.get("value")
#         # This is the key line:
#         new_is_edited = form.cleaned_data.get("is_edited")

#         manager.save_value(
#             new_raw_value=new_value,
#             is_edited=new_is_edited
#         )
