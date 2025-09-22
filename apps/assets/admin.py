from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, ModelForm
from django import forms

from assets.models.asset import Asset
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType


# ✅ Custom Admin Form for Asset — dynamic validation
class AssetAdminForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["symbol", "asset_type", "name"]

    def clean(self):
        cleaned_data = super().clean()
        asset_type = cleaned_data.get("asset_type")
        symbol = cleaned_data.get("symbol")
        name = cleaned_data.get("name")

        # Normalize symbol to uppercase if present
        if symbol:
            cleaned_data["symbol"] = symbol.upper()

        # -----------------------
        # Domain-specific rules
        # -----------------------

        if asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.METAL,
            DomainType.BOND,
        }:
            if not symbol:
                raise forms.ValidationError(
                    "Symbol is required for this asset type.")
            # name is fetched via service — not required on creation

        elif asset_type in {
            DomainType.REAL_ESTATE,
            DomainType.CUSTOM,
        }:
            if not name:
                raise forms.ValidationError(
                    "Name is required for real estate or custom assets.")
            # symbol is optional

        return cleaned_data


# ✅ Inline for EquityDetail — shown only for EQUITY assets
class EquityDetailInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get("DELETE", False):
                asset = form.instance.asset
                if asset.asset_type != DomainType.EQUITY:
                    raise ValidationError(
                        "EquityDetail can only be attached to equity assets.")


class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    formset = EquityDetailInlineFormSet
    extra = 0
    can_delete = False
    max_num = 1


# ✅ Main Asset Admin
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    form = AssetAdminForm

    list_display = ("symbol", "name", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("symbol", "name")

    inlines = [EquityDetailInline]

    def get_inline_instances(self, request, obj=None):
        # Only show equity inline for equity assets
        inlines = []
        for inline_class in self.inlines:
            if obj and obj.asset_type == DomainType.EQUITY:
                inlines.append(inline_class(self.model, self.admin_site))
        return inlines

    def get_readonly_fields(self, request, obj=None):
        # Make `name` read-only for API-fetched asset types (equity, crypto, etc.)
        if obj and obj.asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.BOND,
            DomainType.METAL,
        }:
            return ("name",)
        return ()
