from django.contrib import admin
from .models import Portfolio, InvestmentTheme, FXRate, StockPortfolio


@admin.register(Portfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ['profile', 'created_at',]
    # inlines = [StockPortfolioInline]


@admin.register(InvestmentTheme)
class InvestmentThemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'portfolio', 'parent', 'full_path']
    list_filter = ['portfolio']
    search_fields = ['name']

    def full_path(self, obj):
        return str(obj)
    full_path.short_description = "Full Path"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('portfolio', 'parent')


@admin.register(FXRate)
class FXRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency',
                    'rate', 'updated_at', 'is_stale')
    search_fields = ('from_currency', 'to_currency')
    list_filter = ('from_currency', 'to_currency', 'updated_at')
    readonly_fields = ('updated_at',)

    def is_stale(self, obj):
        return obj.is_stale()
    is_stale.boolean = True
    is_stale.short_description = "Stale (>24h)"


"""
NEW STUFF
"""
# ------------------------------- Stock Portfolio ------------------------------ #


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
