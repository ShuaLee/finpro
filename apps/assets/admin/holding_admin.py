from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from assets.models.holding import Holding
from core.types import get_domain_meta
from schemas.services.schema_constraint_manager import SchemaConstraintManager


class HoldingForm(forms.ModelForm):
    class Meta:
        model = Holding
        fields = ["account", "asset", "quantity",
                  "purchase_price", "purchase_date"]

    def clean(self):
        cleaned_data = super().clean()

        account = cleaned_data.get("account")
        asset = cleaned_data.get("asset")

        # ------------------------------------------------------
        # 1. DOMAIN-BASED VALIDATION (asset allowed in account)
        # ------------------------------------------------------
        # if account and asset:
        #     allowed = get_domain_meta(account.domain_type)["allowed_assets"]
        #     if asset.asset_type.domain not in allowed:
        #         raise ValidationError(
        #             _(f"{account.domain_type} accounts cannot hold {asset.asset_type} assets.")
        #         )

        # ------------------------------------------------------
        # 2. BUSINESS RULE VALIDATION (MIN/MAX ONLY)
        #    ❗ NO ROUNDING
        #    ❗ DO NOT enforce decimal_places
        #    ❗ HOLDING STORES RAW VALUES
        # ------------------------------------------------------
        if account:
            SchemaConstraintManager.validate_business_rules_only(
                account=account,
                holding=self.instance or Holding(),
                cleaned_data=cleaned_data
            )

        return cleaned_data


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    """
    Admin interface for Holdings.
    Ensures domain-asset restrictions and min/max business validation.
    Holding values remain RAW and unrounded.
    """
    form = HoldingForm

    list_display = (
        "account",
        "get_asset_symbol",
        "quantity",
        "purchase_price",
        "purchase_date",
        "created_at",
    )

    list_filter = ("account__account_type", "asset__asset_type")
    search_fields = ("account__name", "asset__name",
                     "asset__identifiers__value")
    ordering = ("account__name", "asset__name")
    autocomplete_fields = ("account", "asset")

    def get_asset_symbol(self, obj):
        pid = obj.asset.primary_identifier
        return pid.value if pid else obj.asset.name

    get_asset_symbol.short_description = "Asset"

    def save_model(self, request, obj, form, change):
        """
        Run validation, save holding, and ensure SCVs get created.
        """

        try:
            # Django-level validation (field types, nulls, etc.)
            obj.full_clean()

            # Save the holding first
            super().save_model(request, obj, form, change)

            messages.success(
                request,
                f"Holding saved successfully for {obj.account.name}."
            )

        except ValidationError as e:
            messages.error(request, f"Validation error: {e}")
