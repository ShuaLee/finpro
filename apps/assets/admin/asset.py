from django.contrib import admin
from django.core.exceptions import ValidationError

from assets.models.asset_core import Asset, AssetIdentifier
from assets.models.pricing import AssetPrice
from assets.models.pricing.extensions import EquityPriceExtension
from assets.models.profiles.equity_profile import EquityProfile

# =========================
# INLINES
# =========================


class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 1
    fields = ("id_type", "value", "is_primary")
    ordering = ("-is_primary",)


class AssetPriceInline(admin.StackedInline):
    model = AssetPrice
    extra = 0
    max_num = 1


class EquityPriceExtensionInline(admin.StackedInline):
    model = EquityPriceExtension
    extra = 0
    max_num = 1


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
        "primary_identifier",
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
            inlines.append(EquityPriceExtensionInline(
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
