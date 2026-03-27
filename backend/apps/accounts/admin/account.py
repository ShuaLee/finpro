from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q

from accounts.models.account import Account
from accounts.models.account_type import AccountType
from accounts.models.audit import AccountAuditEvent
from accounts.models.brokerage import BrokerageConnection
from accounts.models.reconciliation import ReconciliationIssue
from accounts.models.secret import BrokerageSecret
from accounts.models.transaction import AccountTransaction
from accounts.models.job import AccountJob
from accounts.services.account_deletion_service import AccountDeletionService
from accounts.services.account_service import AccountService


def _reset_column_visibility_for_account(account):
    try:
        from schemas.services.mutations import SchemaMutationService
    except Exception:
        return False
    SchemaMutationService.reset_account_to_defaults(account=account)
    return True


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


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "portfolio",
        "name",
        "account_type",
        "enforce_restrictions",
        "position_mode",
        "allow_manual_overrides",
        "created_at",
        "last_synced",
    )
    list_filter = ("account_type", "enforce_restrictions", "position_mode", "created_at")
    search_fields = ("name", "portfolio__name", "portfolio__profile__user__email")
    ordering = ("portfolio", "name")
    readonly_fields = ("created_at", "last_synced")
    actions = ["reset_column_visibility"]
    filter_horizontal = ("allowed_asset_types",)

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

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "portfolio",
                    "name",
                    "account_type",
                )
            },
        ),
        (
            "Default Holding Behavior",
            {
                "fields": (
                    "position_mode",
                    "allow_manual_overrides",
                ),
                "description": "These act as account defaults. Individual holdings can now override how they are tracked and priced.",
            },
        ),
        (
            "Supported Asset Types",
            {
                "fields": (
                    "allowed_asset_types",
                    "enforce_restrictions",
                ),
                "description": "Leave supported asset types empty to allow anything. Turn on strict enforcement only when the account should block incompatible assets.",
            },
        ),
        (
            "Schema",
            {
                "fields": ("schema",),
                "description": "Optional account-level schema override. Otherwise the account falls back to the selected asset type schema.",
            },
        ),
        (
            "Sync",
            {
                "fields": ("last_synced", "created_at"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
            if not change:
                AccountService.initialize_account(account=obj)
                self.message_user(
                    request,
                    f"Account '{obj.name}' created.",
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


@admin.register(BrokerageConnection)
class BrokerageConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "source_type",
        "provider",
        "status",
        "last_synced_at",
        "updated_at",
    )
    list_filter = ("source_type", "provider", "status")
    search_fields = ("account__name", "account__portfolio__profile__user__email", "external_account_id", "connection_label")
    ordering = ("-updated_at",)
    readonly_fields = ("access_token_ref", "last_synced_at", "last_error", "created_at", "updated_at")


@admin.register(AccountTransaction)
class AccountTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "event_type",
        "source",
        "external_transaction_id",
        "traded_at",
        "created_at",
    )
    list_filter = ("event_type", "source")
    search_fields = ("account__name", "external_transaction_id", "note")
    ordering = ("-traded_at", "-id")


@admin.register(ReconciliationIssue)
class ReconciliationIssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "issue_code",
        "severity",
        "status",
        "created_at",
    )
    list_filter = ("issue_code", "severity", "status")
    search_fields = ("account__name", "message")
    ordering = ("-created_at",)


@admin.register(AccountAuditEvent)
class AccountAuditEventAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "actor", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("account__name", "action")
    ordering = ("-created_at",)


@admin.register(AccountJob)
class AccountJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "connection",
        "job_type",
        "status",
        "attempts",
        "max_attempts",
        "created_at",
    )
    list_filter = ("job_type", "status")
    search_fields = ("account__name", "idempotency_key")
    ordering = ("created_at", "id")


@admin.register(BrokerageSecret)
class BrokerageSecretAdmin(admin.ModelAdmin):
    list_display = ("id", "reference", "provider", "is_active", "created_at")
    list_filter = ("provider", "is_active")
    search_fields = ("reference",)
    readonly_fields = ("reference", "provider", "secret_ciphertext", "created_at", "updated_at")
