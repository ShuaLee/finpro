from django.contrib import admin
from .models import Stock, StockAccount, StockTag, StockHolding, StockPortfolio


class StockTagInline(admin.TabularInline):
    model = StockTag
    fk_name = 'parent'
    extra = 1  # Number of empty forms to show for creating new tags


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ['get_user_email', 'created_at']

    # Fields to search by
    search_fields = ['portfolio__profile__user__email']

    # Fields to filter by
    list_filter = ['created_at']

    # Make these fields read-only in the detail view
    readonly_fields = ['portfolio', 'created_at']

    # Custom method for list_display
    def get_user_email(self, obj):
        return obj.portfolio.profile.user.email
    get_user_email.short_description = "User Email"


@admin.register(StockTag)
class StockTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_holding', 'parent')
    search_fields = ('name',)

    # Add the inline for managing sub-tags
    inlines = [StockTagInline]


# StockHolding Inline for StockAccount
class StockHoldingInline(admin.TabularInline):
    model = StockHolding
    extra = 1
    fields = ('stock', 'shares')


# StockAccount Admin
@admin.register(StockAccount)
class StockAccountAdmin(admin.ModelAdmin):
    # Changed 'portfolio' to 'stock_portfolio'
    list_display = ['account_name', 'account_type',
                    'stock_portfolio', 'created_at']
    list_filter = ['account_type', 'stock_portfolio']  # Updated
    search_fields = ['account_name', 'stock_portfolio__name']

# Stock Admin


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'account_count')
    search_fields = ('ticker',)
    ordering = ('ticker',)

    def account_count(self, obj):
        return obj.stock_accounts.count()
    account_count.short_description = "Accounts Holding"

# StockHolding Admin (optional, for direct access)


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ['stock', 'stock_account', 'shares', 'purchase_price']
    # Updated to new relationship
    list_filter = ['stock_account__stock_portfolio']
