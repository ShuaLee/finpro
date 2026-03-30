from django.contrib import admin
from django.db import models
from assets.models.core import Asset, AssetType


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "created_by",
        "is_system",
    )

    search_fields = ("name", "slug")
    ordering = ("name",)

    readonly_fields = ("slug",)

    def is_system(self, obj):
        return obj.created_by is None
    is_system.boolean = True
    is_system.short_description = "System"

    # ----------------------------------
    # Queryset scoping
    # ----------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(
            models.Q(created_by=request.user.profile)
            | models.Q(created_by__isnull=True)
        )

    # ----------------------------------
    # Form behavior
    # ----------------------------------
    def get_readonly_fields(self, request, obj=None):
        ro = list(self.readonly_fields)

        # System asset types are fully immutable
        if obj and obj.created_by is None:
            ro.extend(["name", "created_by"])

        return ro

    # ----------------------------------
    # Save behavior
    # ----------------------------------
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.profile
        super().save_model(request, obj, form, change)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at")
