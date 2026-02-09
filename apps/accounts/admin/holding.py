from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError

from accounts.models.holding import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


# =================================================
# Form
# =================================================

class HoldingAdminForm(forms.ModelForm):
    """
    Admin form for Holding.
    Enforces invariants via model.clean(), but adds UX hints.
    """

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


# =================================================
# Admin
# =================================================

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
        "created_at",
        "updated_at",
    )

    list_filter = (
        "account__portfolio",
        "account__account_type",
        "asset__asset_type",
    )

    search_fields = (
        "asset__id",
        "account__name",
        "account__portfolio__name",
    )

    ordering = (
        "account",
        "asset",
    )

    readonly_fields = (
        "original_ticker",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "account",
        "asset",
    )

    fieldsets = (
        (None, {
            "fields": (
                "account",
                "asset",
            )
        }),
        ("Position", {
            "fields": (
                "quantity",
                "average_purchase_price",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    # -------------------------------------------------
    # Permissions
    # -------------------------------------------------
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        SCVRefreshService.holding_changed(obj)
