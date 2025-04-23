from django.contrib import admin
from .models import Portfolio, InvestmentTheme


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
