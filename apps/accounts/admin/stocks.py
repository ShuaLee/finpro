from django.contrib import admin
from accounts.models.stocks import SelfManagedAccount, ManagedAccount


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_portfolio', 'created_at')
    list_filter = ('name',)
    search_fields = ('name',)
    autocomplete_fields = ['stock_portfolio']  # drop active_schema here
    exclude = ('broker', 'currency',
               'tax_status', 'account_type')
    readonly_fields = ('created_at', 'last_synced', 'currency')


@admin.register(ManagedAccount)
class ManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'broker', 'account_type', 'tax_status',
                    'strategy', 'currency', 'stock_portfolio', 'created_at')
    list_filter = ('account_type',
                   'tax_status', 'currency')
    search_fields = ('name', 'strategy')
    autocomplete_fields = ['stock_portfolio',]
    readonly_fields = ('created_at', 'last_synced')
