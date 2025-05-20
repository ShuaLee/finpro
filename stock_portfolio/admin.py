from django.contrib import admin
from .models import StockPortfolio, SelfManagedAccount


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
