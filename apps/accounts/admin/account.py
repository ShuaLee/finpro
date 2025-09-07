from django.contrib import admin
from accounts.models.account import Account, AccountType
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)


class StockSelfManagedDetailsInline(admin.StackedInline):
    model = StockSelfManagedDetails
    extra = 0
    can_delete = False


class StockManagedDetailsInline(admin.StackedInline):
    model = StockManagedDetails
    extra = 0
    can_delete = False


class CustomAccountDetailsInline(admin.StackedInline):
    model = CustomAccountDetails
    extra = 0
    can_delete = False


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "get_type_display",
                    "subportfolio", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("name", "subportfolio__portfolio__profile__user__email")
    ordering = ["subportfolio", "name"]
    readonly_fields = ("created_at", "last_synced")

    def get_inlines(self, request, obj=None):
        """Show detail inline depending on account type."""
        if not obj:
            return []
        if obj.type == AccountType.STOCK_SELF_MANAGED:
            return [StockSelfManagedDetailsInline]
        elif obj.type == AccountType.STOCK_MANAGED:
            return [StockManagedDetailsInline]
        elif obj.type == AccountType.CUSTOM:
            return [CustomAccountDetailsInline]
        return []
