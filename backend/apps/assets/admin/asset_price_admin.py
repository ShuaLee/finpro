from django.contrib import admin

from apps.assets.models import AssetPrice


@admin.register(AssetPrice)
class AssetPriceAdmin(admin.ModelAdmin):
    list_display = ("asset", "price", "change", "volume", "source", "as_of")
    list_filter = ("source",)
    search_fields = ("asset__name", "asset__symbol")
    readonly_fields = ("as_of",)
