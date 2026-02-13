from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ("email", "is_email_verified", "is_active", "is_staff", "date_joined")
    search_fields = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Verification", {"fields": ("email_verified_at",)}),
        ("Security", {"fields": ("failed_login_count", "locked_until")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    readonly_fields = ("date_joined", "last_login")
    filter_horizontal = ("groups", "user_permissions")

    def is_email_verified(self, obj):
        return obj.is_email_verified
    is_email_verified.boolean = True
