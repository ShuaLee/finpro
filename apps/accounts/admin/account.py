from django.contrib import admin, messages
from django import forms

from accounts.models.account import Account
from accounts.models.account_type import AccountType
from accounts.models.account_classification import (
    ClassificationDefinition,
    AccountClassification,
)
from accounts.services.account_service import AccountService
from fx.models.country import Country


# =================================================
# Forms
# =================================================

class ClassificationDefinitionForm(forms.ModelForm):
    """
    Admin-safe form:
    - Country queryset is injected at runtime
    - Avoids app-registry import issues
    """

    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.none(),  # ✅ placeholder
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 12}),
        help_text="Countries where this classification applies.",
    )

    class Meta:
        model = ClassificationDefinition
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Safe: executed after app registry is ready
        self.fields["countries"].queryset = Country.objects.all()

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("all_countries"):
            cleaned["countries"] = Country.objects.none()

        return cleaned



class AccountTypeForm(forms.ModelForm):
    """
    Custom form for AccountType admin:
    - prevents editing protected fields on system types
    """

    class Meta:
        model = AccountType
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        instance = self.instance

        if instance and instance.pk and instance.is_system:
            for field in ("slug", "is_system"):
                if cleaned.get(field) != getattr(instance, field):
                    self.add_error(
                        field,
                        "System account types cannot be modified."
                    )

        return cleaned


# =================================================
# Admin
# =================================================

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    form = AccountTypeForm

    list_display = (
        "id",
        "name",
        "slug",
        "allows_multiple",
        "is_system",
    )

    list_filter = (
        "is_system",
        "allows_multiple",
    )

    search_fields = (
        "name",
        "slug",
    )

    ordering = ("name",)

    filter_horizontal = ("allowed_asset_types",)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_system:
            return ("slug", "is_system")
        return ()


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
    Account admin:
    - Uses definition at creation time
    - Delegates classification logic to AccountService
    """

    list_display = (
        "id",
        "portfolio",
        "name",
        "account_type",
        "classification",
        "created_at",
        "last_synced",
    )

    list_filter = ("account_type", "created_at")

    search_fields = (
        "name",
        "portfolio__name",
        "portfolio__profile__user__username",
        "portfolio__profile__user__email",
    )

    ordering = ("portfolio", "name")

    readonly_fields = (
        "created_at",
        "classification",
        "last_synced",
    )

    # -------------------------------------------------
    # Dynamic form
    # -------------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        """
        Define form dynamically to avoid circular imports.
        """

        class AccountForm(forms.ModelForm):
            definition = forms.ModelChoiceField(
                queryset=ClassificationDefinition.objects.all(),
                required=True,
                label="Account Definition",
                help_text="Select a classification definition (e.g. TFSA, RRSP).",
            )

            class Meta:
                model = Account
                fields = (
                    "portfolio",
                    "name",
                    "account_type",
                    "broker",
                    "definition",
                )

        kwargs["form"] = AccountForm
        return super().get_form(request, obj, **kwargs)

    # -------------------------------------------------
    # Save logic
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Create Account, then initialize classification exactly once.
        """

        definition = form.cleaned_data.get("definition")
        if not definition:
            self.message_user(
                request,
                "A classification definition is required.",
                level=messages.ERROR,
            )
            return

        try:
            # Let Account.save() handle validation
            super().save_model(request, obj, form, change)

            AccountService.initialize_account(
                account=obj,
                definition=definition,
                profile=obj.portfolio.profile,
            )

            self.message_user(
                request,
                f"Account '{obj.name}' linked to '{definition.name}'.",
                level=messages.SUCCESS,
            )

        except Exception as exc:
            self.message_user(
                request,
                f"Error creating account: {exc}",
                level=messages.ERROR,
            )
