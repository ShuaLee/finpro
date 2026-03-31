from django.contrib import admin

from apps.users.models import AuthEvent


@admin.register(AuthEvent)
class AuthEventAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "event_type",
        "ip_address",
        "created_at",
    )
    list_filter = ("event_type", "created_at")
    search_fields = ("user__email", "ip_address", "user_agent")
    readonly_fields = (
        "user",
        "event_type",
        "ip_address",
        "user_agent",
        "metadata",
        "created_at",
    )

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

