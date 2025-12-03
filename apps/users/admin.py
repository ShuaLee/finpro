# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.translation import gettext_lazy as _
# from users.models import User, Profile
# from users.services.profile_service import ProfileService


# class ProfileInline(admin.StackedInline):
#     """Inline Profile editor inside User admin."""
#     model = Profile
#     can_delete = False
#     verbose_name_plural = "Profile"
#     fk_name = "user"
#     extra = 0
#     fields = ("full_name", "country", "currency", "plan", "account_type")


# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     """Custom User admin using email instead of username."""
#     ordering = ["id"]
#     list_display = ["email", "is_active", "is_staff", "last_login"]
#     list_filter = ["is_active", "is_staff", "is_superuser"]
#     search_fields = ["email"]
#     readonly_fields = ["last_login", "date_joined"]

#     # Fields for detail view
#     fieldsets = (
#         (None, {"fields": ("email", "password")}),
#         (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
#         (_("Important dates"), {"fields": ("last_login", "date_joined")}),
#     )

#     # Fields for add user form
#     add_fieldsets = (
#         (None, {
#             "classes": ("wide",),
#             "fields": ("email", "password1", "password2", "is_active", "is_staff", "is_superuser"),
#         }),
#     )

#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#         # Ensure profile exists after saving
#         ProfileService.bootstrap(obj)

#     inlines = [ProfileInline]


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     """Standalone Profile admin for advanced editing."""
#     list_display = ["user", "full_name", "country", "currency", "plan", "account_type"]
#     list_filter = ["country", "plan", "account_type"]
#     search_fields = ["user__email", "full_name"]
#     ordering = ["user__email"]
