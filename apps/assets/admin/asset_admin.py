from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.crypto_detail import CryptoDetail
from assets.models.details.equity_detail import EquityDetail
from assets.models.market_data_cache import MarketDataCache
from assets.services.syncs.asset_sync import AssetSyncService

from core.types import DomainType


class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 0
    can_delete = False
    readonly_fields = ("id_type", "value", "is_primary")

class MarketDataCacheInline(admin.StackedInline):
    model = MarketDataCache
    extra = 0
    can_delete = False
    max_num = 1
    readonly_fields = [
        f.name for f in MarketDataCache._meta.fields if f.name not in ("id", "asset")
    ]

class CryptoDetailInline(admin.StackedInline):
    model = CryptoDetail
    extra = 0
    can_delete = False
    max_num = 1
    readonly_fields = [
        f.name for f in CryptoDetail._meta.fields if f.name not in ("id", "asset")
    ]

class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    extra = 0
    can_delete = False
    max_num = 1
    readonly_fields = [
        f.name for f in EquityDetail._meta.fields if f.name not in ("id", "asset")]


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Read-only asset viewer. Assets cannot be added/edited directly."""

    list_display = ("get_primary_identifier", "name", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("name", "identifiers__value")

    # Base inlines — always included
    base_inlines = [AssetIdentifierInline, MarketDataCacheInline]

    # Dynamic inline injection
    def get_inline_instances(self, request, obj=None):
        inline_instances = []

        # Always show these
        for inline_class in self.base_inlines:
            inline_instances.append(inline_class(self.model, self.admin_site))

        if obj:
            if obj.asset_type == DomainType.EQUITY:
                inline_instances.append(EquityDetailInline(self.model, self.admin_site))
            elif obj.asset_type == DomainType.CRYPTO:
                inline_instances.append(CryptoDetailInline(self.model, self.admin_site))
            # If you ever add METAL/BOND, you plug their detail inline here.

        return inline_instances

    # ------------------------------
    # Permissions
    # ------------------------------
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # ------------------------------
    # Helpers
    # ------------------------------
    def get_primary_identifier(self, obj):
        primary = obj.identifiers.filter(is_primary=True).first()
        return primary.value if primary else "-"
    get_primary_identifier.short_description = "Identifier"

    # ------------------------------
    # Admin Actions
    # ------------------------------
    actions = ["sync_profile", "sync_quote"]

    def sync_profile(self, request, queryset):
        success, fail = 0, 0
        for asset in queryset:
            if AssetSyncService.sync(asset, profile=True):
                success += 1
            else:
                fail += 1

        self.message_user(
            request,
            f"Profile sync completed: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )
    sync_profile.short_description = "Sync profile from FMP"

    def sync_quote(self, request, queryset):
        success, fail = 0, 0
        for asset in queryset:
            if AssetSyncService.sync(asset, profile=False):
                success += 1
            else:
                fail += 1

        self.message_user(
            request,
            f"Quote sync completed: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )
    sync_quote.short_description = "Sync quote from FMP"