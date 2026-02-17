from django.contrib import admin

from users.models import PasswordResetToken


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "consumed_at", "created_at")
    list_filter = ("consumed_at",)
    search_fields = ("user__email", "token_hash")
    readonly_fields = ("token_hash", "created_at")
