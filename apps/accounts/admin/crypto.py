from django.contrib import admin
from accounts.models.crypto import CryptoWallet

@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    list_display = ("name", "get_user_email", "crypto_portfolio", "created_at")
    search_fields = ("name",)
    autocomplete_fields = ["crypto_portfolio"]
    readonly_fields = ("created_at", "last_synced")

    def get_user_email(self, obj):
        return obj.crypto_portfolio.portfolio.profile.user.email
    get_user_email.short_description = "User Email"