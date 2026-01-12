# from django.contrib import admin
# from schemas.models.constraints import MasterConstraint, SchemaConstraint


# @admin.register(MasterConstraint)
# class MasterConstraintAdmin(admin.ModelAdmin):
#     """
#     Admin configuration for system-level reusable constraint templates.
#     """
#     list_display = (
#         "label",
#         "name",
#         "applies_to",
#         "default_value",
#         "min_limit",
#         "max_limit",
#         "is_editable",
#         "is_active",
#     )
#     list_filter = ("applies_to", "is_editable", "is_active")
#     search_fields = ("name", "label", "description")
#     ordering = ("applies_to", "label")

#     fieldsets = (
#         (None, {
#             "fields": (
#                 "name",
#                 "label",
#                 "description",
#                 "applies_to",
#             )
#         }),
#         ("Default & Range", {
#             "fields": (
#                 "default_value",
#                 ("min_limit", "max_limit"),
#             )
#         }),
#         ("Meta", {
#             "fields": ("is_editable", "is_active")
#         }),
#     )


# @admin.register(SchemaConstraint)
# class SchemaConstraintAdmin(admin.ModelAdmin):
#     """
#     Admin for per-column constraints attached to a specific SchemaColumn.
#     """
#     list_display = (
#         "column",
#         "label",
#         "value",
#         "applies_to",
#         "min_limit",
#         "max_limit",
#         "is_editable",
#     )
#     list_filter = ("applies_to", "is_editable")
#     search_fields = ("name", "label", "column__identifier",
#                      "column__schema__account_type")
#     ordering = ("column__schema__account_type", "column__identifier", "label")

#     autocomplete_fields = ("column",)

#     fieldsets = (
#         (None, {
#             "fields": (
#                 "column",
#                 ("name", "label"),
#                 "applies_to",
#             )
#         }),
#         ("Constraint Values", {
#             "fields": (
#                 "value",
#                 ("min_limit", "max_limit"),
#             )
#         }),
#         ("Meta", {
#             "fields": ("is_editable",)
#         }),
#     )
