# from django.contrib import admin
# from django.contrib.admin.widgets import AdminTextareaWidget
# from django.forms import JSONField as DjangoJSONFormField

# from schemas.models.template import SchemaTemplate, SchemaTemplateColumn


# # Pretty JSON widget (optional, but MUCH cleaner)
# class PrettyJSONWidget(AdminTextareaWidget):
#     def format_value(self, value):
#         import json
#         if not value:
#             return ""
#         try:
#             return json.dumps(value, indent=4, sort_keys=True)
#         except Exception:
#             return value


# # ===============================
# # INLINE FOR TEMPLATE COLUMNS
# # ===============================
# class SchemaTemplateColumnInline(admin.TabularInline):
#     model = SchemaTemplateColumn
#     extra = 0

#     fields = (
#         "title",
#         "identifier",
#         "data_type",
#         "source",
#         "source_field",
#         "is_editable",
#         "is_deletable",
#         "is_system",
#         "display_order",
#         "constraints",        # 👈 Add JSON field here
#     )

#     formfield_overrides = {
#         DjangoJSONFormField: {"widget": PrettyJSONWidget},
#     }


# # ===============================
# # TEMPLATE ADMIN
# # ===============================


# @admin.register(SchemaTemplate)
# class SchemaTemplateAdmin(admin.ModelAdmin):
#     list_display = ("name", "account_type", "is_active", "created_at")
#     list_filter = ("is_active",)
#     search_fields = ("name", "account_type")
#     inlines = [SchemaTemplateColumnInline,]


# # ===============================
# # TEMPLATE COLUMN ADMIN (Standalone)
# # ===============================
# @admin.register(SchemaTemplateColumn)
# class SchemaTemplateColumnAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "identifier",
#         "template",
#         "data_type",
#         "source",
#         "formula",
#         "is_default",
#         "is_system",
#         "is_editable",
#         "display_order",
#     )
#     list_filter = ("data_type", "source", "is_default",
#                    "is_system", "is_editable")
#     search_fields = ("title", "identifier", "template__name", "source_field")
#     ordering = ("template", "display_order", "title")
#     autocomplete_fields = ("template", "formula",)

#     formfield_overrides = {
#         DjangoJSONFormField: {"widget": PrettyJSONWidget},
#     }

#     fieldsets = (
#         (None, {
#             "fields": (
#                 "template",
#                 "title",
#                 "identifier",
#                 "data_type",
#                 "source",
#                 "source_field",
#             )
#         }),
#         ("Display & Behavior", {
#             "fields": (
#                 "is_default",
#                 "is_editable",
#                 "is_deletable",
#                 "is_system",
#                 "display_order",
#             ),
#         }),
#         ("Constraints (JSON)", {
#             "fields": ("constraints",),  # 👈 Add editable JSON here
#         }),
#     )
