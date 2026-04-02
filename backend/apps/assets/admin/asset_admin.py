from django.contrib import admin

from apps.assets.models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "symbol",
        "asset_type",
        "owner",
        "is_public",
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
    readonly_fields = (
        "id",
        "is_public",
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
