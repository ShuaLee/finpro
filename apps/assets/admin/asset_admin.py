from django.contrib import admin
from assets.models.asset import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Minimal admin for the base Asset model.
    Hidden from the menu, used only for autocomplete (HoldingAdmin).
    """
    search_fields = ("symbol", "name")
    list_display = ("id", "symbol", "name", "asset_type")

    def has_module_permission(self, request):
        """
        Hide this admin section from the sidebar.
        Still allows autocomplete to work.
        """
        return False
