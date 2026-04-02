from django.contrib import admin

from apps.assets.models import AssetType


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "created_by",
        "is_system",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "slug", "description", "created_by__user__email")
    readonly_fields = ("slug", "created_at", "updated_at", "is_system")
    ordering = ("name",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "created_by",
                    "description",
                    "is_system",
                )
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
