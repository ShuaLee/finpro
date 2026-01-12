# import nested_admin

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.translation import gettext_lazy as _

# from users.models import User
# from users.services.profile_service import ProfileService

# # Import our modular inline
# from .inlines.profile_inline import ProfileInline


# class UserAdmin(nested_admin.NestedModelAdmin, BaseUserAdmin):
#     """
#     Custom User admin using email instead of username.
#     This version now pulls in ProfileInline from the new admin package.
#     """

#     ordering = ["id"]
#     list_display = ["email", "is_active", "is_staff", "last_login"]
#     list_filter = ["is_active", "is_staff", "is_superuser"]
#     search_fields = ["email"]
#     readonly_fields = ["last_login", "date_joined"]

#     # ------------------------
#     # Detail (change) view
#     # ------------------------
#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         (_("Permissions"), {
#          "fields": ("is_active", "is_staff", "is_superuser")}),
#         (_("Important dates"), {"fields": ("last_login", "date_joined")}),
#     )

#     # ------------------------
#     # Add user form
#     # ------------------------
#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": (
#                     "email",
#                     "password1",
#                     "password2",
#                     "is_active",
#                     "is_staff",
#                     "is_superuser",
#                 ),
#             },
#         ),
#     )

#     # ------------------------
#     # Ensure profile is created
#     # ------------------------
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#         ProfileService.bootstrap(obj)

#     # ------------------------
#     # Inline stack (so far only Profile)
#     # ------------------------
#     inlines = [ProfileInline]


# # Register the custom user admin
# admin.site.register(User, UserAdmin)
