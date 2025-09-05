from django.contrib import admin
from portfolios.models import Portfolio, StockPortfolio, CryptoPortfolio, MetalPortfolio, CustomPortfolio

# inlines


class StockPortfolioInline(admin.StackedInline):
    model = StockPortfolio
    extra = 0
    can_delete = False
    read_only_fields = ["created_at"]
    verbose_name_plural = "Stock Portfolio"


class CryptoPortfolioInline(admin.StackedInline):
    model = CryptoPortfolio
    extra = 0
    can_delete = False
    read_only_fields = ["created_at"]
    verbose_name_plural = "Crypto Portfolio"


class MetalPortfolioInline(admin.StackedInline):
    model = MetalPortfolio
    extra = 0
    can_delete = False
    read_only_fields = ["created_at"]
    verbose_name_plural = "Metal Portfolio"


class StockPortfolioInline(admin.StackedInline):
    model = CustomPortfolio
    extra = 0
    can_delete = False
    read_only_fields = ["created_at"]
    verbose_name_plural = "Custom Portfolio"


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["id", "get_email", "created_at"]
    search_fields = ["profile__user__email"]
    list_filter = ["created_at"]

    def get_email(self, obj):
        return obj.profile.user.email
    get_email.short_description = "User Email"
    get_email.admin_order_field = "profile__user__email"
