import nested_admin

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models.holdings.holding import Holding
from schemas.services.schema_constraint_manager import SchemaConstraintManager
from users.admin.inlines.scv_inline import SCVInline


class HoldingInlineForm(forms.ModelForm):
    """
    Inline-safe HoldingForm
    - No domain enforcement (accounts already filtered)
    - Only business rule validation (min/max)
    - Does not mutate decimals or round values
    - Avoids admin double-validation issues
    """

    class Meta:
        model = Holding
        fields = [
            "asset",
            "quantity",
            "purchase_price",
            "purchase_date",
        ]

    def clean(self):
        cleaned_data = super().clean()

        account = self.instance.account or cleaned_data.get("account")
        asset = cleaned_data.get("asset")

        # If account is missing (nested inline creates blank row), skip validation
        if not account:
            return cleaned_data

        # ------------------------------------------------------
        # BUSINESS RULE VALIDATION ONLY
        # No rounding, no decimal enforcement
        # ------------------------------------------------------
        try:
            SchemaConstraintManager.validate_business_rules_only(
                account=account,
                holding=self.instance or Holding(),
                cleaned_data=cleaned_data,
            )
        except ValidationError as e:
            raise ValidationError({"quantity": e})  # anchor the error nicely

        return cleaned_data


class HoldingInline(nested_admin.NestedStackedInline):
    model = Holding
    fk_name = "account"
    form = HoldingInlineForm
    extra = 1
    show_change_link = True

    fields = (
        "asset",
        "quantity",
        "purchase_price",
        "purchase_date",
        "created_at",
    )

    readonly_fields = ("created_at",)
    autocomplete_fields = ("asset",)

    inlines = [SCVInline]
