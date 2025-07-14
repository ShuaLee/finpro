from django.contrib import admin
from .models import FXRate

# Register your models here.
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