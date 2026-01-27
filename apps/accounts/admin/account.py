from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models.account import Account
from accounts.models.account_type import AccountType
from accounts.models.account_classification import (
    ClassificationDefinition,
    AccountClassification,
)
from accounts.services.account_service import AccountService
from accounts.services.account_deletion_service import AccountDeletionService
from fx.models.country import Country
from schemas.services.account_column_visibility_service import (
    AccountColumnVisibilityService,
)


# =================================================
# Forms
# =================================================

class ClassificationDefinitionForm(forms.ModelForm):
    """
    Admin-safe form:
    - Country queryset injected at runtime
    - Avoids app-registry import issues
    """

    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.none(),  # placeholder
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 12}),
        help_text="Countries where this classification applies.",
    )

    class Meta:
        model = ClassificationDefinition
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["countries"].queryset = Country.objects.all()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("all_countries"):
            cleaned["countries"] = Country.objects.none()
        return cleaned


class AccountTypeForm(forms.ModelForm):
    class Meta:
        model = AccountType
        fields = "__all__"

    def clean_allowed_asset_types(self):
        asset_types = self.cleaned_data.get("allowed_asset_types")
        owner = self.cleaned_data.get("owner")
        is_system = self.cleaned_data.get("is_system")

        if not asset_types:
            return asset_types

        # System AccountTypes may ONLY use system AssetTypes
        if is_system:
            invalid = asset_types.exclude(created_by__isnull=True)
            if invalid.exists():
                names = ", ".join(invalid.values_list("name", flat=True))
                raise ValidationError(
                    f"System account types cannot use user asset types: {names}"
                )

        # User AccountTypes may use system OR owned AssetTypes
        else:
            invalid = asset_types.exclude(
                Q(created_by__isnull=True) | Q(created_by=owner)
            )
            if invalid.exists():
                names = ", ".join(invalid.values_list("name", flat=True))
                raise ValidationError(
                    f"You cannot use asset types you do not own: {names}"
                )

        return asset_types


# =================================================
# Admin
# =================================================

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    """
    AccountType admin rules:
    - slug is never editable
    - is_system is editable on CREATE, immutable on EDIT
    """

    form = AccountTypeForm
    exclude = ("slug",)

    list_display = (
        "id",
        "name",
        "slug",
        "is_system",
    )

    list_filter = (
        "is_system",
    )

    search_fields = ("name",)
    ordering = ("name",)

    filter_horizontal = ("allowed_asset_types",)

    def get_readonly_fields(self, request, obj=None):
        # is_system locked after creation
        if obj:
            return ("is_system",)
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
    - Classification definition chosen at creation
    - Classification initialized via AccountService
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

    actions = [
        "reset_column_visibility",
    ]

    # -------------------------------------------------
    # Admin action
    # -------------------------------------------------
    @admin.action(description="Reset column visibility to defaults")
    def reset_column_visibility(self, request, queryset):
        for account in queryset:
            AccountColumnVisibilityService.reset_account_to_defaults(
                account=account
            )

        self.message_user(
            request,
            "Column visibility reset to defaults.",
            level=messages.SUCCESS,
        )

    # -------------------------------------------------
    # Dynamic form
    # -------------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        """
        Dynamic form avoids circular imports and
        ensures definition is only used on create.
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
        definition = form.cleaned_data.get("definition")

        if not definition:
            self.message_user(
                request,
                "A classification definition is required.",
                level=messages.ERROR,
            )
            return

        try:
            # 1️⃣ Save the Account itself
            super().save_model(request, obj, form, change)

            # 2️⃣ Initialize ONLY on creation
            if not change:
                AccountService.initialize_account(
                    account=obj,
                    definition=definition,
                )

                self.message_user(
                    request,
                    f"Account '{obj.name}' initialized with '{definition.name}'.",
                    level=messages.SUCCESS,
                )

        except Exception as exc:
            self.message_user(
                request,
                f"Error creating account: {exc}",
                level=messages.ERROR,
            )

    def delete_model(self, request, obj):
        """
        Ensure schema cleanup when deleting a single account.
        """
        AccountDeletionService.delete_account(account=obj)

        self.message_user(
            request,
            f"Account '{obj.name}' deleted.",
            level=messages.SUCCESS,
        )

    def delete_queryset(self, request, queryset):
        """
        Ensure schema cleanup when deleting multiple accounts.
        """
        count = queryset.count()

        for account in queryset.select_related(
            "portfolio", "account_type"
        ):
            AccountDeletionService.delete_account(account=account)

        self.message_user(
            request,
            f"{count} account(s) deleted.",
            level=messages.SUCCESS,
        )

