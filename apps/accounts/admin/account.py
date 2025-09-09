from django.contrib import admin

from accounts.models.account import Account
from accounts.models.details import (
    StockSelfManagedDetails,
    StockManagedDetails,
    CustomAccountDetails,
)
from accounts.services.detail_model_resolver import get_account_details_models


# -------------------------------
# Inline classes
# -------------------------------
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


# Registry mapping model -> inline
DETAIL_INLINE_MAP = {
    StockSelfManagedDetails: StockSelfManagedDetailsInline,
    StockManagedDetails: StockManagedDetailsInline,
    CustomAccountDetails: CustomAccountDetailsInline,
}


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "get_type_display", "subportfolio", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("name", "subportfolio__portfolio__profile__user__email")
    ordering = ["subportfolio", "name"]
    readonly_fields = ("created_at", "last_synced")

    def get_inlines(self, request, obj=None):
        """
        Dynamically return the inline(s) based on the account's DomainType.
        Uses the resolver to find eligible detail models.
        """
        if not obj:
            return []

        inlines = []
        for model in get_account_details_models(obj.type):
            inline = DETAIL_INLINE_MAP.get(model)
            if inline:
                inlines.append(inline)

        return inlines
