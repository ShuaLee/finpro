from django.contrib import admin
from assets.models.classifications import Exchange


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country", "is_system")
    list_filter = ("country", "is_system")
    search_fields = ("code", "name")
    readonly_fields = ("is_system",)
