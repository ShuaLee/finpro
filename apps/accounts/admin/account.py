from django.contrib import admin
from django import forms
from accounts.models.account import Account
from accounts.models.account_classification import ClassificationDefinition, AccountClassification
from accounts.services.account_service import AccountService


# ----------------------------
# Admin Registrations
# ----------------------------
@admin.register(ClassificationDefinition)
class ClassificationDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tax_status",
                    "jurisdiction", "is_system", "created_at")
    list_filter = ("tax_status", "jurisdiction", "is_system")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at",)


@admin.register(AccountClassification)
class AccountClassificationAdmin(admin.ModelAdmin):
    list_display = (
        "id", "profile", "definition", "contribution_limit", "carry_forward_room", "created_at",
    )
    list_filter = ("definition__tax_status", "definition__jurisdiction")
    search_fields = ("definition__name",
                     "profile__user__username", "profile__user__email")
    ordering = ("profile", "definition__name")
    readonly_fields = ("created_at",)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = (
        "id", "portfolio", "name", "account_type", "classification",
        "broker", "created_at", "last_synced",
    )
    list_filter = ("account_type", "broker", "created_at")
    search_fields = (
        "name", "portfolio__name",
        "portfolio__profile__user__username",
        "portfolio__profile__user__email",
    )
    ordering = ("portfolio", "name")
    readonly_fields = ("created_at", "last_synced")

    def get_form(self, request, obj=None, **kwargs):
        from django import forms  # lazy import
        from accounts.models.account import Account  # ensure model is loaded

        class AccountForm(forms.ModelForm):
            definition = forms.ModelChoiceField(
                queryset=ClassificationDefinition.objects.all(),
                required=False,
                help_text="Pick a definition (e.g., TFSA, RRSP). The system will attach/create the classification."
            )

            class Meta:
                model = Account
                fields = "__all__"  # let Django resolve lazily

            def save(self, commit=True):
                account = super().save(commit=False)
                definition = self.cleaned_data.get("definition")
                if definition:
                    account = AccountService.assign_classification(
                        account, definition, account.portfolio.profile
                    )
                if commit:
                    account.save()
                    self.save_m2m()
                return account

        kwargs["form"] = AccountForm
        return super().get_form(request, obj, **kwargs)
