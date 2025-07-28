from django.contrib import admin
from accounts.models.stocks import SelfManagedAccount, ManagedAccount


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'broker', 'account_type', 'tax_status', 'stock_portfolio', 'created_at')
    list_filter = ('broker', 'account_type', 'tax_status')
    search_fields = ('name', 'broker')
    autocomplete_fields = ['stock_portfolio', 'active_schema']
    readonly_fields = ('created_at', 'last_synced')


@admin.register(ManagedAccount)
class ManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'broker', 'account_type', 'tax_status', 'strategy', 'currency', 'stock_portfolio', 'created_at')
    list_filter = ('account_type', 'tax_status', 'currency')
    search_fields = ('name', 'strategy')
    autocomplete_fields = ['stock_portfolio', 'active_schema']
    readonly_fields = ('created_at', 'last_synced')
