from django.contrib import admin

from profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "full_name",
        "currency",
        "country",
        "plan",
        "account_type",
        "onboarding_status",
        "created_at",
    )
    list_filter = (
        "currency",
        "country",
        "plan",
        "account_type",
        "onboarding_status",
    )
    search_fields = ("user__email", "full_name")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email
