from django.contrib import admin

from apps.assets.models import Asset, AssetDividendSnapshot, AssetMarketData, AssetPrice


class AssetMarketDataInline(admin.StackedInline):
    model = AssetMarketData
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_synced_at",
        "last_successful_sync_at",
    )


class AssetPriceInline(admin.StackedInline):
    model = AssetPrice
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ("as_of",)


class AssetDividendSnapshotInline(admin.StackedInline):
    model = AssetDividendSnapshot
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ("last_computed_at", "created_at", "updated_at")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "symbol",
        "asset_type",
        "owner",
        "is_public",
        "is_market_tracked",
        "current_price",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "asset_type",
        "is_active",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "symbol",
        "description",
        "owner__user__email",
    )
    inlines = (AssetMarketDataInline, AssetPriceInline, AssetDividendSnapshotInline)
    readonly_fields = (
        "id",
        "is_public",
        "is_market_tracked",
        "current_price",
        "created_at",
        "updated_at",
    )
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "asset_type",
                    "owner",
                    "name",
                    "symbol",
                    "description",
                    "is_active",
                    "is_public",
                    "is_market_tracked",
                    "current_price",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("data",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
