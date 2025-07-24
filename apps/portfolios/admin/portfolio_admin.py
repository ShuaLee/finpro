from django.contrib import admin
from portfolios.models import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """
    Admin for the main Portfolio model.
    """
    list_display = ['profile', 'created_at']
    search_fields = ['profile__user__email']
    list_filter = ['created_at']
