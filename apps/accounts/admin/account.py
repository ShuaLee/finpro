from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models.account import Account
from accounts.models.account_classification import (
    AccountClassification,
    ClassificationDefinition,
)
from accounts.models.account_type import AccountType
from accounts.services.account_deletion_service import AccountDeletionService
from accounts.services.account_service import AccountService
from fx.models.country import Country


def _reset_column_visibility_for_account(account):
    try:
        from schemas.services.mutations import SchemaMutationService
    except Exception:
        return False
    SchemaMutationService.reset_account_to_defaults(account=account)
    return True


class ClassificationDefinitionForm(forms.ModelForm):
    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.none(),
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

        if is_system:
            invalid = asset_types.exclude(created_by__isnull=True)
            if invalid.exists():
                names = ", ".join(invalid.values_list("name", flat=True))
                raise ValidationError(
                    f"System account types cannot use user asset types: {names}"
                )
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


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    form = AccountTypeForm
    exclude = ("slug",)
    list_display = ("id", "name", "slug", "is_system")
    list_filter = ("is_system",)
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("allowed_asset_types",)

    def get_readonly_fields(self, request, obj=None):
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
        "profile__user__email",
    )
    ordering = ("profile", "definition__name")
    readonly_fields = ("created_at",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
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
    search_fields = ("name", "portfolio__name", "portfolio__profile__user__email")
    ordering = ("portfolio", "name")
    readonly_fields = ("created_at", "classification", "last_synced")
    actions = ["reset_column_visibility"]

    @admin.action(description="Reset column visibility to defaults")
    def reset_column_visibility(self, request, queryset):
        updated = 0
        skipped = 0
        for account in queryset:
            ok = _reset_column_visibility_for_account(account)
            if ok:
                updated += 1
            else:
                skipped += 1
        if updated:
            self.message_user(
                request,
                f"Column visibility reset for {updated} account(s).",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} account(s): schemas app unavailable.",
                level=messages.WARNING,
            )

    def get_form(self, request, obj=None, **kwargs):
        class AccountForm(forms.ModelForm):
            definition = forms.ModelChoiceField(
                queryset=ClassificationDefinition.objects.all(),
                required=obj is None,
                label="Account Definition",
                help_text="Select a classification definition (e.g. TFSA, RRSP).",
            )

            class Meta:
                model = Account
                fields = ("portfolio", "name", "account_type", "broker", "definition")

        kwargs["form"] = AccountForm
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        definition = form.cleaned_data.get("definition")

        if not change and not definition:
            self.message_user(
                request,
                "A classification definition is required on creation.",
                level=messages.ERROR,
            )
            return

        try:
            super().save_model(request, obj, form, change)
            if not change:
                AccountService.initialize_account(account=obj, definition=definition)
                self.message_user(
                    request,
                    f"Account '{obj.name}' initialized with '{definition.name}'.",
                    level=messages.SUCCESS,
                )
        except Exception as exc:
            self.message_user(
                request,
                f"Error creating/updating account: {exc}",
                level=messages.ERROR,
            )

    def delete_model(self, request, obj):
        AccountDeletionService.delete_account(account=obj)
        self.message_user(
            request,
            f"Account '{obj.name}' deleted.",
            level=messages.SUCCESS,
        )

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        for account in queryset.select_related("portfolio", "account_type"):
            AccountDeletionService.delete_account(account=account)
        self.message_user(
            request,
            f"{count} account(s) deleted.",
            level=messages.SUCCESS,
        )
