# from django.contrib import admin, messages
# from django.shortcuts import redirect
# from django.template.response import TemplateResponse
# from django.urls import path, reverse
# from schemas.models import (
#     Schema,
#     SchemaColumn,
# )
# from schemas.services.holding_sync_service import sync_schema_column_to_holdings
# from .forms import AddBuiltInColumnForm, SchemaColumnInlineForm
# from .utils import build_builtin_choices_for_schema


# class SchemaColumnInline(admin.TabularInline):
#     model = SchemaColumn
#     form = SchemaColumnInlineForm
#     extra = 0
#     fields = (
#         "custom_title",
#         "title", "data_type",
#         "source", "source_field", "field_path",
#         "editable", "is_deletable",
#         "is_system", "scope",
#         "display_order", "investment_theme",
#     )

#     ordering = ("display_order",)
#     show_change_link = True

#     def get_formset(self, request, obj=None, **kwargs):
#         FormClass = self.form
#         choices, disabled, config = build_builtin_choices_for_schema(obj)

#         class DynamicForm(FormClass):
#             _builtin_choices = choices
#             _builtin_disabled = disabled
#             _config = config

#         kwargs["form"] = DynamicForm
#         return super().get_formset(request, obj, **kwargs)


# @admin.register(Schema)
# class SchemaAdmin(admin.ModelAdmin):
#     list_display = ("id", "name", "schema_type",
#                     "content_type", "object_id", "created_at")
#     search_fields = ("name", "schema_type")
#     list_filter = ("schema_type", "content_type")
#     readonly_fields = ("created_at",)
#     inlines = [SchemaColumnInline]
#     change_form_template = "admin/schemas/schema/change_form.html"

#     def save_formset(self, request, form, formset, change):
#         instances = formset.save()
#         if formset.model is SchemaColumn:
#             for obj in getattr(formset, "new_objects", []):
#                 sync_schema_column_to_holdings(obj)
#         return instances

#     def get_urls(self):
#         urls = super().get_urls()
#         custom = [
#             path(
#                 "<int:object_id>/add_builtin/",
#                 self.admin_site.admin_view(self.add_builtin_view),
#                 name="schemas_schema_add_builtin",
#             )
#         ]
#         return custom + urls

#     def add_builtin_view(self, request, object_id):
#         schema = self.get_object(request, object_id)
#         if not schema:
#             self.message_user(request, "Schema not found.",
#                               level=messages.ERROR)
#             return redirect("admin:schemas_schema_changelist")

#         if request.method == "POST":
#             form = AddBuiltInColumnForm(request.POST, schema=schema)
#             if form.is_valid():
#                 col, created = form.create_column()
#                 if created:
#                     sync_schema_column_to_holdings(col)
#                     self.message_user(
#                         request, f"Added built-in column “{col.title}”.")
#                 else:
#                     self.message_user(
#                         request, "That column already exists.", level=messages.WARNING)
#                 return redirect(reverse("admin:schemas_schema_change", args=[schema.pk]))
#         else:
#             form = AddBuiltInColumnForm(schema=schema)

#         context = {
#             **self.admin_site.each_context(request),
#             "opts": self.model._meta,
#             "original": schema,
#             "title": "Add built-in column",
#             "form": form,
#             "media": self.media + form.media,
#             "has_view_permission": True,
#             "has_change_permission": True,
#             "add_builtin_url": request.path,
#             "return_url": reverse("admin:schemas_schema_change", args=[schema.pk]),
#         }
#         return TemplateResponse(request, "admin/schemas/schema/add_builtin.html", context)
