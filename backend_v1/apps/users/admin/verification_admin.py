from django.contrib import admin, messages

from users.models import EmailVerificationToken
from users.services.email_verification_service import EmailVerificationService


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "purpose", "expires_at", "consumed_at", "created_at")
    list_filter = ("purpose", "consumed_at")
    search_fields = ("user__email", "token_hash")
    readonly_fields = ("token_hash", "created_at")
    actions = ["resend_verification_email"]

    @admin.action(description="Resend verification email for selected users")
    def resend_verification_email(self, request, queryset):
        sent = 0
        for token in queryset.select_related("user"):
            user = token.user
            if user.is_email_verified:
                continue

            try:
                code, _ = EmailVerificationService.issue_token(user=user)
                EmailVerificationService.send_verification_email(
                    user=user,
                    verification_code=code,
                )
                sent += 1
            except Exception:
                continue

        self.message_user(
            request,
            f"Verification emails sent: {sent}",
            level=messages.SUCCESS,
        )
