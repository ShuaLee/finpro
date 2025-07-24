from django.contrib import admin
from portfolios.models import MetalPortfolio


@admin.register(MetalPortfolio)
class MetalPortfolioAdmin(admin.ModelAdmin):
    """
    Admin for the MetalPortfolio model.
    """
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']
    list_filter = ['created_at']
