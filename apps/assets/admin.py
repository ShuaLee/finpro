from django.contrib import admin
from assets.models.asset import Asset, Holding


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "symbol", "name", "asset_type",
                    "created_at", "updated_at")
    list_filter = ("asset_type", "created_at")
    search_fields = ("symbol", "name")
    ordering = ("asset_type", "symbol")


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "asset", "quantity",
                    "purchase_price", "purchase_date", "created_at")
    list_filter = ("asset__asset_type", "purchase_date")
    search_fields = ("asset__symbol", "asset__name", "account__name")
    raw_id_fields = ("account", "asset")
