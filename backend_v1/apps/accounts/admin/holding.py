from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from accounts.models.holding import Holding
from accounts.models.holding_snapshot import HoldingSnapshot


def _notify_holding_changed(holding):
    try:
        from schemas.services.orchestration import SchemaOrchestrationService
    except Exception:
        return
    SchemaOrchestrationService.holding_changed(holding)


class HoldingAdminForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get("quantity")
        avg_price = cleaned.get("average_purchase_price")
        if quantity == 0 and avg_price is not None:
            raise ValidationError(
                "Average purchase price must be empty when quantity is zero."
            )
        return cleaned


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    form = HoldingAdminForm
    list_display = (
        "id",
        "account",
        "asset",
        "original_ticker",
        "quantity",
        "average_purchase_price",
        "tracking_mode",
        "price_source_mode",
        "created_at",
        "updated_at",
    )
    list_filter = ("account__portfolio", "account__account_type", "asset__asset_type")
    search_fields = ("asset__id", "account__name", "account__portfolio__name")
    ordering = ("account", "asset")
    readonly_fields = ("original_ticker", "created_at", "updated_at")
    autocomplete_fields = ("account", "asset")

    fieldsets = (
        (None, {"fields": ("account", "asset")}),
        (
            "Position",
            {
                "fields": (
                    "quantity",
                    "average_purchase_price",
                    "tracking_mode",
                    "price_source_mode",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _notify_holding_changed(obj)


@admin.register(HoldingSnapshot)
class HoldingSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "holding",
        "as_of",
        "quantity",
        "price",
        "value_profile_currency",
        "source",
    )
    list_filter = ("source",)
    search_fields = ("holding__account__name", "holding__asset__id")
    ordering = ("-as_of", "-id")
