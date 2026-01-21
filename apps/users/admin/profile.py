# users/admin/profile.py

from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models.profile import Profile

User = get_user_model()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # -------------------------
    # List view
    # -------------------------
    list_display = (
        "user_email",
        "full_name",
        "currency",
        "country",
        "plan",
        "account_type",
        "receive_email_updates",
        "created_at",
    )

    list_select_related = (
        "user",
        "currency",
        "country",
        "plan",
        "account_type",
    )

    list_filter = (
        "currency",
        "country",
        "plan",
        "account_type",
        "receive_email_updates",
    )

    search_fields = (
        "user__email",
        "full_name",
    )

    ordering = ("-created_at",)

    # -------------------------
    # Detail view
    # -------------------------
    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("User", {
            "fields": (
                "user",
            )
        }),
        ("Identity", {
            "fields": (
                "full_name",
                "birth_date",
            )
        }),
        ("Preferences", {
            "fields": (
                "language",
                "currency",
                "country",
            )
        }),
        ("Subscription", {
            "fields": (
                "plan",
                "account_type",
            )
        }),
        ("Notifications", {
            "fields": (
                "receive_email_updates",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )

    # -------------------------
    # Helpers
    # -------------------------
    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj: Profile):
        return obj.user.email
