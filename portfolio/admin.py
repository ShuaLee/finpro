from django.contrib import admin
from portfolio.models import IndividualPortfolio
# Register your models here.


@admin.register(IndividualPortfolio)
class IndividualPortfolioAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'created_at')
    search_fields = ('profile__user__email', 'name')
