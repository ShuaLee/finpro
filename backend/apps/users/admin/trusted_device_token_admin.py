from django.contrib import admin
from django.utils import timezone

from apps.users.models import TrustedDeviceToken


@admin.register(TrustedDeviceToken)
class TrustedDeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "is_valid",
        "last_used_at",
        "expires_at",
        "revoked_at",
        "created_at",
    )
    list_filter = ("expires_at", "revoked_at", "created_at")
    search_fields = ("user__email", "token_hash")
    readonly_fields = (
        "user",
        "token_hash",
        "expires_at",
        "last_used_at",
        "revoked_at",
        "created_at",
        "is_valid",
        "is_expired",
        "is_revoked",
    )
    actions = ("revoke_selected_devices",)

    @admin.display(description="Email", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email

    @admin.display(boolean=True, description="Valid")
    def is_valid(self, obj):
        return obj.is_valid

    @admin.display(boolean=True, description="Expired")
    def is_expired(self, obj):
        return obj.is_expired

    @admin.display(boolean=True, description="Revoked")
    def is_revoked(self, obj):
        return obj.is_revoked

    @admin.action(description="Revoke selected trusted devices")
    def revoke_selected_devices(self, request, queryset):
        count = queryset.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())
        self.message_user(request, f"Revoked {count} trusted device(s).")

    def has_add_permission(self, request):
        return False
