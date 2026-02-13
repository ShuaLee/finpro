from django.contrib import admin

from users.models import EmailVerificationToken


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "expires_at", "consumed_at", "created_at")
    list_filter = ("purpose", "consumed_at")
    search_fields = ("user__email", "token_hash")
    readonly_fields = ("token_hash", "created_at")
