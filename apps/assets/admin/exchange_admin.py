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
        "owner",
    )

    list_filter = ("is_system", "country")
    search_fields = ("code", "name", "country__name", "country__code")

    readonly_base = ("id", "slug", "created_at", "is_system", "owner")

    def get_readonly_fields(self, request, obj=None):
        """Superusers can edit everything; staff get locked system records."""
        if request.user.is_superuser:
            return self.readonly_base  # only structural fields locked

        # staff: if system → fully locked
        if obj and obj.is_system:
            return self.readonly_base + (
                "code",
                "name",
                "country",
                "symbol_suffix",
                "delay",
            )

        # staff editing user-created → lock id/slug/system fields only
        return self.readonly_base

    def has_delete_permission(self, request, obj=None):
        """Only superusers or user-owned custom entries may be deleted."""
        if request.user.is_superuser:
            return True

        if obj and obj.owner == request.user.profile:
            return True

        return False

    def has_add_permission(self, request):
        """Only superusers can manually add exchanges."""
        return request.user.is_superuser
