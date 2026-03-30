from django.contrib import admin

from apps.users.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "full_name",
        "language",
        "timezone",
        "currency",
        "country_code",
        "created_at",
    )
    list_filter = ("language", "timezone", "currency", "country_code")
    search_fields = ("user__email", "full_name")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email
