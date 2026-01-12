# from django.contrib import admin
# from datatype.models import (
#     ConstraintType,
#     ConstraintDefinition,
#     AppliedConstraint,
# )


# class ConstraintDefinitionInline(admin.TabularInline):
#     """
#     Allows viewing system default constraints for each ConstraintType.
#     Read-only because definitions are system-managed.
#     """
#     model = ConstraintDefinition
#     extra = 0
#     can_delete = False

#     readonly_fields = (
#         "data_type",
#         "default_value",
#         "is_system",
#     )

#     fields = (
#         "data_type",
#         "default_value",
#         "is_system",
#     )


# @admin.register(ConstraintType)
# class ConstraintTypeAdmin(admin.ModelAdmin):

#     list_display = (
#         "id",
#         "name",
#         "slug",
#         "value_data_type",
#         "is_system",
#     )

#     list_filter = ("is_system", "value_data_type")
#     search_fields = ("name", "slug", "description")
#     ordering = ("slug",)

#     filter_horizontal = ("applies_to",)

#     inlines = [ConstraintDefinitionInline]

#     readonly_fields = ("is_system",)

#     fieldsets = (
#         ("Basic Info", {
#             "fields": ("name", "slug", "description")
#         }),
#         ("Applicability", {
#             "fields": ("applies_to", "value_data_type")
#         }),
#         ("System", {
#             "fields": ("is_system",),
#             "classes": ("collapse",),
#         }),
#     )

#     def get_readonly_fields(self, request, obj=None):
#         if obj and obj.is_system:
#             return (
#                 "slug",
#                 "value_data_type",
#                 "applies_to",
#                 "is_system",
#             )
#         return self.readonly_fields


# @admin.register(ConstraintDefinition)
# class ConstraintDefinitionAdmin(admin.ModelAdmin):

#     list_display = (
#         "id",
#         "data_type",
#         "constraint_type",
#         "default_value",
#         "is_system",
#     )

#     list_filter = (
#         "data_type",
#         "constraint_type",
#         "is_system",
#     )

#     search_fields = (
#         "default_value",
#         "constraint_type__name",
#         "data_type__name",
#     )

#     ordering = ("data_type__slug", "constraint_type__slug")

#     readonly_fields = ("is_system",)

#     def get_readonly_fields(self, request, obj=None):
#         if obj and obj.is_system:
#             return (
#                 "data_type",
#                 "constraint_type",
#                 "default_value",
#                 "is_system",
#             )
#         return self.readonly_fields


# @admin.register(AppliedConstraint)
# class AppliedConstraintAdmin(admin.ModelAdmin):

#     list_display = (
#         "id",
#         "schema_column",
#         "constraint_type",
#         "value",
#         "is_user_defined",
#     )

#     list_filter = (
#         "constraint_type",
#         "schema_column__schema__account_type",
#         "is_user_defined",
#     )

#     search_fields = (
#         "schema_column__identifier",
#         "constraint_type__name",
#         "value",
#     )

#     ordering = ("schema_column",)

#     raw_id_fields = ("schema_column", "constraint_type")
