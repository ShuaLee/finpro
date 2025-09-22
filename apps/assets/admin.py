from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django import forms
from django.forms import BaseInlineFormSet

from assets.models.assets import Asset, AssetIdentifier
from assets.models.details.equity_detail import EquityDetail
from core.types import DomainType
from assets.services.syncs.asset_sync import AssetSyncService
from assets.services.syncs.equity_sync import EquitySyncService  # <- your single-stock creation service


# ✅ Inline for AssetIdentifier
class AssetIdentifierInline(admin.TabularInline):
    model = AssetIdentifier
    extra = 1
    min_num = 1
    can_delete = True


# ✅ Inline for EquityDetail
class EquityDetailInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if not form.cleaned_data.get("DELETE", False):
                asset = form.instance.asset
                if asset.asset_type != DomainType.EQUITY:
                    raise ValidationError(
                        "EquityDetail can only be attached to equity assets."
                    )


class EquityDetailInline(admin.StackedInline):
    model = EquityDetail
    formset = EquityDetailInlineFormSet
    extra = 0
    can_delete = False
    max_num = 1


# ✅ Custom Asset Form
class AssetAdminForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_type", "name", "currency"]

    def clean(self):
        cleaned_data = super().clean()
        asset_type = cleaned_data.get("asset_type")
        name = cleaned_data.get("name")

        # Tradables → must have identifier (enforced inline)
        if asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.METAL,
            DomainType.BOND,
        }:
            pass

        # Non-tradables → must have name
        elif asset_type in {DomainType.REAL_ESTATE, DomainType.CUSTOM}:
            if not name:
                raise forms.ValidationError(
                    "Name is required for real estate or custom assets."
                )

        return cleaned_data


# ✅ Helper to show identifier
def _display_identifier(asset: Asset) -> str:
    primary_id = asset.identifiers.filter(is_primary=True).first()
    return primary_id.value if primary_id else "-"


# ✅ Main Admin
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    form = AssetAdminForm

    list_display = ("get_primary_identifier", "name", "asset_type", "created_at")
    list_filter = ("asset_type",)
    search_fields = ("name", "identifiers__value")

    inlines = [AssetIdentifierInline, EquityDetailInline]

    # --- Actions ---
    actions = ["sync_profile", "sync_quote"]

    def get_inline_instances(self, request, obj=None):
        """Show detail inlines only when applicable."""
        inlines = []
        for inline_class in self.inlines:
            if inline_class.model == EquityDetail:
                if obj and obj.asset_type == DomainType.EQUITY:
                    inlines.append(inline_class(self.model, self.admin_site))
            else:
                inlines.append(inline_class(self.model, self.admin_site))
        return inlines

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.asset_type in {
            DomainType.EQUITY,
            DomainType.CRYPTO,
            DomainType.BOND,
            DomainType.METAL,
        }:
            return ("name",)
        return ()

    def get_primary_identifier(self, obj):
        return _display_identifier(obj)
    get_primary_identifier.short_description = "Identifier"

    # --- Custom Actions ---
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
