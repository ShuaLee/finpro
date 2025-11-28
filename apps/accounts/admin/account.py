from django.contrib import admin, messages
from django import forms
from accounts.models.account import Account
from accounts.models.account_classification import ClassificationDefinition, AccountClassification
from accounts.services.account_service import AccountService
from fx.models.country import Country


class ClassificationDefinitionForm(forms.ModelForm):

    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 12}),
        help_text="Countries where this classification applies.",
    )

    class Meta:
        model = ClassificationDefinition
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("all_countries"):
            # If all_countries=True → ignore any selected countries
            cleaned["countries"] = Country.objects.none()

        return cleaned


# ----------------------------
# Admin
# ----------------------------

@admin.register(ClassificationDefinition)
class ClassificationDefinitionAdmin(admin.ModelAdmin):
    form = ClassificationDefinitionForm

    list_display = (
        "id",
        "name",
        "tax_status",
        "display_scope",
        "is_system",
        "created_at",
    )
    list_filter = ("tax_status", "is_system")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
    ordering = ("name",)

    def display_scope(self, obj):
        """Show either 'All Countries' or the country list."""
        if obj.all_countries:
            return "All Countries"

        codes = list(obj.countries.values_list("code", flat=True))
        return ", ".join(codes) if codes else "N/A"

    display_scope.short_description = "Jurisdictions"


@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "profile",
        "definition",
        "contribution_limit",
        "carry_forward_room",
        "created_at",
    )
    list_filter = ("definition__tax_status",)
    search_fields = (
        "definition__name",
        "profile__user__username",
        "profile__user__email",
    )
    ordering = ("profile", "definition__name")
    readonly_fields = ("created_at",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """
    Custom admin for Account:
    - Dynamically defines AccountForm to avoid circular model loading
    - Enforces classification assignment via AccountService
    """

    list_display = (
        "id", "portfolio", "name", "account_type",
        "classification", "created_at", "last_synced",
    )
    list_filter = ("account_type", "created_at")
    search_fields = (
        "name", "portfolio__name",
        "portfolio__profile__user__username",
        "portfolio__profile__user__email",
    )
    ordering = ("portfolio", "name")
    readonly_fields = ("created_at", "classification", "last_synced")

    # ----------------------------
    # Dynamic form definition
    # ----------------------------
    def get_form(self, request, obj=None, **kwargs):
        """
        Define AccountForm dynamically so it's loaded only
        after all related models (like Portfolio) are ready.
        """

        class AccountForm(forms.ModelForm):
            definition = forms.ModelChoiceField(
                queryset=ClassificationDefinition.objects.all(),
                required=True,
                help_text="Select a classification definition (e.g., TFSA, RRSP, 401k).",
                label="Account Definition",
            )

            class Meta:
                model = Account
                fields = [
                    "portfolio",
                    "name",
                    "account_type",
                    "broker",
                    "definition",
                ]

        kwargs["form"] = AccountForm
        return super().get_form(request, obj, **kwargs)

    # ----------------------------
    # Save logic
    # ----------------------------
    def save_model(self, request, obj, form, change):
        """
        Ensure every Account has a valid classification.
        Uses AccountService.assign_classification() for consistency.
        """

        definition = form.cleaned_data.get("definition")

        if not definition:
            self.message_user(
                request,
                "A definition is required to create an account.",
                level=messages.ERROR,
            )
            return

        try:
            # Save the base account first
            obj.save()

            # Assign classification atomically
            AccountService.initialize_account(
                account=obj,
                definition=definition,
                profile=obj.portfolio.profile,
            )

            self.message_user(
                request,
                f"Account '{obj.name}' created and linked to '{definition.name}'.",
                level=messages.SUCCESS,
            )

        except Exception as e:
            self.message_user(
                request,
                f"Error assigning classification: {e}",
                level=messages.ERROR,
            )
