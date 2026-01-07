from django.contrib import admin
from django.core.exceptions import ValidationError

from assets.admin.base.base_price_extension import BasePriceExtensionInline
from assets.models.asset_core import Asset, AssetIdentifier
from assets.models.events.equity.dividend_extensions import EquityDividendExtension
from assets.models.events import EquityDividendEvent
from assets.models.pricing import AssetPrice
from assets.models.pricing.extensions import EquityPriceExtension
from assets.models.profiles.equity_profile import EquityProfile

# =========================
# INLINES
# =========================


class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 1
    fields = ("id_type", "value",)


class AssetPriceInline(admin.StackedInline):
    model = AssetPrice
    extra = 0
    max_num = 1


class EquityPriceExtensionInline(BasePriceExtensionInline):
    model = EquityPriceExtension


class EquityDividendExtensionInline(admin.StackedInline):
    model = EquityDividendExtension
    extra = 0
    max_num = 1
    can_delete = False
    verbose_name = "Dividend Summary"
    verbose_name_plural = "Dividend Summary"

    readonly_fields = (
        "trailing_dividend_12m",
        "forward_dividend",
        "last_computed",
    )

    fields = readonly_fields


class EquityDividendEventInline(admin.TabularInline):
    model = EquityDividendEvent
    extra = 0
    can_delete = False
    show_change_link = True

    ordering = ("-ex_date",)

    fields = (
        "ex_date",
        "dividend",
        "adj_dividend",
        "payment_date",
        "record_date",
        "frequency",
        "yield_value",
        "created_at",
    )

    readonly_fields = fields


class EquityProfileInline(admin.StackedInline):
    model = EquityProfile
    extra = 0
    max_num = 1
    verbose_name = "Equity Profile"
    verbose_name_plural = "Equity Profile"


# =========================
# ASSET ADMIN
# =========================

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "asset_type",
        "display_name",
        "currency",
        "is_custom",
        "created_at",
    )

    list_filter = (
        "asset_type",
        "is_custom",
        "currency",
    )

    search_fields = (
        "identifiers__value",
        "equity_profile__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [
        AssetIdentifierInline,
        AssetPriceInline,
    ]

    fieldsets = (
        ("Core", {
            "fields": (
                "asset_type",
                "currency",
                "is_custom",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # -------------------------
    # Dynamic Inlines by Asset Type
    # -------------------------
    def get_inline_instances(self, request, obj=None):
        """
        Dynamically attach profile/price extensions based on asset_type.
        """
        inlines = super().get_inline_instances(request, obj)

        if not obj:
            return inlines

        if obj.asset_type.slug == "equity":
            inlines.append(EquityProfileInline(self.model, self.admin_site))
            inlines.append(EquityDividendExtensionInline(
                self.model, self.admin_site))
            inlines.append(EquityDividendEventInline(
                self.model, self.admin_site))

        return inlines

    # -------------------------
    # Helpers
    # -------------------------
    @admin.display(description="Name")
    def display_name(self, obj):
        return obj.name

    # -------------------------
    # Validation Hook
    # -------------------------
    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return
        super().save_model(request, obj, form, change)
