from django.contrib import admin
from core.models import Profile
from portfolio.models import Portfolio

# Register your models here.


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'individual_profile',
                    'asset_manager_profile')
