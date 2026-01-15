from django import forms
from django.contrib import admin

from assets.models.core import AssetPrice
from assets.models.real_estate import RealEstateAsset, RealEstateType, RealEstateCashflow


# =====================================================
# Forms
# =====================================================

class RealEstateAssetAdminForm(forms.ModelForm):
    """
    Admin form that exposes AssetPrice fields.
    """

    price = forms.DecimalField(
        max_digits=20,
        decimal_places=6,
        required=False,
        help_text="Current estimated market value.",
    )

    price_source = forms.CharField(
        max_length=50,
        required=False,
        initial="MANUAL",
    )

    class Meta:
        model = RealEstateAsset
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate price fields if AssetPrice exists
        if self.instance.pk and hasattr(self.instance.asset, "price"):
            asset_price = self.instance.asset.price
            self.fields["price"].initial = asset_price.price
            self.fields["price_source"].initial = asset_price.source


# =====================================================
# Inlines
# =====================================================

class RealEstateCashflowInline(admin.StackedInline):
    model = RealEstateCashflow
    extra = 0
    max_num = 1


# =====================================================
# RealEstateType
# =====================================================

@admin.register(RealEstateType)
class RealEstateTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "is_system")
    search_fields = ("name",)
    list_filter = ("created_by",)

    def is_system(self, obj):
        return obj.created_by is None

    is_system.boolean = True


# =====================================================
# RealEstateAsset
# =====================================================

@admin.register(RealEstateAsset)
class RealEstateAssetAdmin(admin.ModelAdmin):
    form = RealEstateAssetAdminForm

    list_display = (
        "property_type",
        "owner",
        "is_owner_occupied",
        "country",
        "currency",
        "display_price",
        "has_cashflow",
    )

    list_filter = (
        "property_type",
        "country",
        "currency",
        "is_owner_occupied",
    )

    search_fields = ("address", "city")

    inlines = (RealEstateCashflowInline,)

    fieldsets = (
        (None, {
            "fields": (
                "owner",
                "property_type",
                "is_owner_occupied",
                "country",
                "city",
                "address",
                "currency",
            )
        }),
        ("Valuation", {
            "fields": (
                "price",
                "price_source",
            )
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
    )

    # -------------------------------------------------
    # Save hooks
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Persist RealEstateAsset AND AssetPrice.
        """
        super().save_model(request, obj, form, change)

        price = form.cleaned_data.get("price")
        source = form.cleaned_data.get("price_source") or "MANUAL"

        if price is not None:
            AssetPrice.objects.update_or_create(
                asset=obj.asset,
                defaults={
                    "price": price,
                    "source": source,
                },
            )

    # -------------------------------------------------
    # Derived fields
    # -------------------------------------------------
    def display_price(self, obj):
        if hasattr(obj.asset, "price"):
            return obj.asset.price.price
        return "—"

    display_price.short_description = "Value"

    def has_cashflow(self, obj):
        return hasattr(obj, "cashflow")

    has_cashflow.boolean = True
