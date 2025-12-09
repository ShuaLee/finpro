from django.contrib import admin
from assets.models.exchanges import Exchange


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "country",
        "symbol_suffix",
        "delay",
        "is_system",
    )

    list_filter = (
        "is_system",
        "country",
    )

    search_fields = (
        "code",
        "name",
        "country__name",
        "country__code",
    )

    readonly_fields = (
        "id",
        "slug",
        "created_at",
        "is_system",
        "owner",
    )

    fieldsets = (
        ("Basic Info", {
            "fields": ("id", "code", "name", "slug"),
        }),

        ("Location", {
            "fields": ("country",),
        }),

        ("FMP Metadata", {
            "fields": ("symbol_suffix", "delay"),
        }),

        ("System", {
            "fields": ("is_system", "owner", "created_at"),
        }),
    )

    ordering = ("code",)

    def has_change_permission(self, request, obj=None):
        """
        Prevent admin from changing system exchanges 
        unless they have superuser privileges.
        """
        if obj and obj.is_system and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deleting system exchanges through admin.
        """
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)
