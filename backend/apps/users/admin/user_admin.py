from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = (
        "email",
        "is_email_verified",
        "is_active",
        "is_staff",
        "failed_login_count",
        "locked_until",
        "date_joined",
    )
    search_fields = ("email",)
    readonly_fields = ("date_joined", "last_login")
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Verification", {"fields": ("email_verified_at",)}),
        ("Security", {"fields": ("failed_login_count", "locked_until")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Timestamps", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_active", "is_staff"),
            },
        ),
    )

    @admin.display(boolean=True, description="Email Verified")
    def is_email_verified(self, obj):
        return obj.is_email_verified
