from django.contrib import admin
from accounts.models import SelfManagedAccount, ManagedAccount

@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "get_user_email", "stock_portfolio", "created_at")
    list_filter = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ['stock_portfolio']
    exclude = ('broker', 'currency', 'tax_status', 'account_type')
    readonly_fields = ('created_at', 'last_synced', 'currency')

    def get_user_email(self, obj):
        return obj.stock_portfolio.portfolio.profile.user.email
    get_user_email.short_description = "User Email"


@admin.register(ManagedAccount)
class ManagedAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name", "get_user_email", "stock_portfolio", "broker",
        "account_type", "tax_status", "strategy", "currency", "created_at"
    )
    list_filter = ("account_type", "tax_status", "currency")
    search_fields = ("name", "strategy")
    autocomplete_fields = ["stock_portfolio"]
    readonly_fields = ("created_at", "last_synced")

    def get_user_email(self, obj):
        return obj.stock_portfolio.portfolio.profile.user.email
    get_user_email.short_description = "User Email"
