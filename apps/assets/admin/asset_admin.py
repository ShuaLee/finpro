from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from assets.models.assets import Asset, AssetIdentifier, AssetType
from assets.models.details.crypto_detail import CryptoDetail
from assets.models.details.equity_detail import EquityDetail
from assets.models.details.real_estate_detail import RealEstateDetail
from assets.models.market_data_cache import MarketDataCache
from assets.services.syncs.asset_sync import AssetSyncService


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "created_by")
    list_filter = ("is_system",)
    search_fields = ("name", "slug")

    readonly_fields = ("is_system", "created_by")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.readonly_fields

        # System-defined types: fully locked
        if obj.is_system:
            return ("name", "slug", "is_system", "created_by")

        # User-created types: cannot edit slug, cannot edit system flags
        return ("slug", "is_system", "created_by")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return True

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)
        else:
            self.message_user(request, "AssetType deleted.",
                              level=messages.SUCCESS)

    # ------------------------------------------------------------
    # Prevent deleting system types
    # ------------------------------------------------------------
    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return True

    # Friendly error messaging in admin
    def delete_model(self, request, obj):
        try:
            obj.delete()
        except ValidationError as e:
            self.message_user(request, str(e), level=messages.ERROR)
        else:
            self.message_user(request, "AssetType deleted.",
                              level=messages.SUCCESS)


# ================================================================
# Inline: Asset Identifiers (always read-only)
# ================================================================
class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 0
    can_delete = False
    readonly_fields = ("id_type", "value", "is_primary")

# ================================================================
# Inline: Market Data Cache (always read-only)
# ================================================================


class MarketDataCacheInline(admin.StackedInline):
    model = MarketDataCache
    extra = 0
    can_delete = False
    max_num = 1

    readonly_fields = [
        f.name for f in MarketDataCache._meta.fields
        if f.name not in ("id", "asset")
    ]


# ================================================================
# Inline: Crypto Detail (quantity_precision editable)
# ================================================================
class CryptoDetailInline(admin.StackedInline):
    model = CryptoDetail
    extra = 0
    can_delete = False
    max_num = 1

    readonly_fields = [
        f.name for f in CryptoDetail._meta.fields
        if f.name not in ("id", "asset", "quantity_precision")
    ]

    fields = [
        "quantity_precision",
        "exchange",
        "description",
        "website",
        "logo_url",
        "is_custom",
        "created_at",
        "last_updated",
    ]


# ================================================================
# Inline: Equity Detail (fully read-only)
# ================================================================
class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    extra = 0
    can_delete = False
    max_num = 1

    readonly_fields = [
        f.name for f in EquityDetail._meta.fields
        if f.name not in ("id", "asset")
    ]


# ================================================================
# Inline: Real Estate Detail (editable)
# ================================================================


class RealEstateDetailInline(admin.StackedInline):
    model = RealEstateDetail
    extra = 0
    can_delete = False
    max_num = 1

    readonly_fields = ("created_at", "last_updated")

    fieldsets = (
        ("Location", {"fields": ("country", "region", "city", "address")}),
        ("Property Type", {"fields": ("property_type",)}),
        ("Valuation", {"fields": ("purchase_price",
         "estimated_value", "appraisal_date")}),
        ("Income / Expenses", {"fields": ("rental_income", "expenses")}),
        ("Mortgage", {
            "fields": (
                "is_mortgaged",
                "mortgage_balance",
                "interest_rate",
                "monthly_mortgage_payment",
            )
        }),
        ("System", {"fields": ("created_at", "last_updated")}),
    )

# ================================================================
# Asset Admin (parent object read-only, inlines editable)
# ================================================================


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Assets are read-only, but inlines may be editable."""

    list_display = ("get_primary_identifier", "name",
                    "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("name", "identifiers__value")

    readonly_fields = [f.name for f in Asset._meta.fields]

    base_inlines = [
        AssetIdentifierInline,
        MarketDataCacheInline,
    ]

    def get_inline_instances(self, request, obj=None):
        inline_instances = []

        # Always show identifiers + market data
        for inline in self.base_inlines:
            inline_instances.append(inline(self.model, self.admin_site))

        if not obj:
            return inline_instances

        slug = obj.asset_type.slug  # <— new correct field

        if slug == "equity":
            inline_instances.append(
                EquityDetailInline(self.model, self.admin_site))

        elif slug == "crypto":
            inline_instances.append(
                CryptoDetailInline(self.model, self.admin_site))

        elif slug == "real_estate":
            inline_instances.append(
                RealEstateDetailInline(self.model, self.admin_site))

        return inline_instances

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True  # Needed for inline editing

    def get_primary_identifier(self, obj):
        pid = obj.identifiers.filter(is_primary=True).first()
        return pid.value if pid else "-"
    get_primary_identifier.short_description = "Identifier"

    # ------------------------
    # Admin Actions
    # ------------------------
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
            f"Profile sync: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )

    def sync_quote(self, request, queryset):
        success, fail = 0, 0
        for asset in queryset:
            if AssetSyncService.sync(asset, profile=False):
                success += 1
            else:
                fail += 1

        self.message_user(
            request,
            f"Quote sync: {success} succeeded, {fail} failed.",
            messages.SUCCESS if fail == 0 else messages.WARNING,
        )
