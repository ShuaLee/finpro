"""

from django.contrib import admin
from accounts.models.metals import StorageFacility
from .models.stocks import SelfManagedAccount, ManagedAccount


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email',
                    'stock_portfolio', 'account_type', 'created_at', 'last_synced')
    list_filter = ('account_type', 'created_at')
    search_fields = ('name', 'stock_portfolio__name',
                     'stock_portfolio__portfolio__profile__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_synced')

    def get_user_email(self, obj):
        try:
            return obj.stock_portfolio.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "stock_portfolio__portfolio__profile__user__email"


@admin.register(ManagedAccount)
class ManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_portfolio', 'current_value',
                    'invested_amount', 'currency', 'created_at')
    search_fields = (
        'name', 'stock_portfolio__portfolio__profile__user__email')
    list_filter = ('stock_portfolio', 'currency')


"""
#METALS
"""


@admin.register(StorageFacility)
class StorageFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email',
                    'created_at', 'last_synced')  # add 'metal_portfolio',
    list_filter = ('created_at',)
    search_fields = ('name', 'metal_portfolio__name',
                     'metal_portfolio__portfolio__profile__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_synced')

    def get_user_email(self, obj):
        try:
            return obj.metal_portfolio.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "metal_portfolio__portfolio__profile__user__email"

    """