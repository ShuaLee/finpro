from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import StockPortfolio, SelfManagedAccount, StockHolding
import logging

logger = logging.getLogger(__name__)


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email', 'currency',
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


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = [
        'holding_link', 'stock_link', 'self_managed_account_link', 'quantity', 'purchase_price',
        'purchase_date', 'current_value', 'performance', 'investment_theme'
    ]
    list_display_links = ['holding_link']
    list_filter = [
        'self_managed_account__stock_portfolio__portfolio__profile',
        'stock__quote_type', 'stock__sector', 'stock__is_adr', 'investment_theme'
    ]
    search_fields = ['stock__ticker',
                     'stock__name', 'self_managed_account__name']
    list_editable = ['quantity', 'purchase_price', 'purchase_date']
    list_per_page = 50
    fields = [
        'self_managed_account', 'stock', 'quantity', 'purchase_price',
        'purchase_date', 'investment_theme'
    ]
    autocomplete_fields = ['stock', 'self_managed_account']
    actions = ['refresh_holding_values']

    def holding_link(self, obj):
        url = reverse('admin:stock_portfolio_stockholding_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, f"{obj.stock.ticker} ({obj.self_managed_account.name})")
    holding_link.short_description = 'Holding'

    def stock_link(self, obj):
        url = reverse('admin:stocks_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock.ticker)
    stock_link.short_description = 'Stock'

    def self_managed_account_link(self, obj):
        url = reverse('admin:stock_portfolio_selfmanagedaccount_change', args=[
                      obj.self_managed_account.id])
        return format_html('<a href="{}">{}</a>', url, obj.self_managed_account.name)
    self_managed_account_link.short_description = 'Account'

    def current_value(self, obj):
        return obj.get_current_value()
    current_value.short_description = 'Current Value'

    def performance(self, obj):
        return f"{obj.get_performance():.2f}%"
    performance.short_description = 'Performance'

    def refresh_holding_values(self, request, queryset):
        updated = 0
        for holding in queryset:
            try:
                if holding.stock.fetch_fmp_data(force_update=True):
                    holding.stock.save()
                    updated += 1
            except Exception as e:
                logger.error(
                    f"Failed to refresh {holding.stock.ticker}: {str(e)}")
        self.message_user(
            request,
            f"Refreshed {updated} holdings' stock values.",
            level='success' if updated else 'warning'
        )
    refresh_holding_values.short_description = "Refresh stock values from FMP"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock', 'self_managed_account', 'investment_theme')
