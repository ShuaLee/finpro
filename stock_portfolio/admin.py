from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from .models import BaseStockAccount, StockPortfolio, StockHolding, SelfManagedAccount, ManagedAccount
from stocks.models import Stock

@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email', 'currency', 'stock_portfolio', 'account_type', 'created_at', 'last_synced')
    list_filter = ('account_type', 'created_at')
    search_fields = ('name', 'stock_portfolio__name', 'stock_portfolio__portfolio__profile__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_synced')

    def get_user_email(self, obj):
        try:
            return obj.stock_portfolio.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "stock_portfolio__portfolio__profile__user__email"


"""
class StockHoldingAdminForm(forms.ModelForm):
    # Dropdown for selecting the Stock
    asset_object_id = forms.ModelChoiceField(
        queryset=Stock.objects.all(),
        label="Stock",
        required=True
    )

    # Custom ChoiceField for selecting the Account (SelfManagedAccount or ManagedAccount)
    account_object_id = forms.ChoiceField(
        choices=(),
        label="Account",
        required=False  # Account is nullable
    )

    class Meta:
        model = StockHolding
        fields = [
            'asset_object_id', 'account_object_id',
            'quantity', 'purchase_price', 'purchase_date', 'investment_theme'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-set content types for generic foreign keys
        self.stock_portfolio_ct = ContentType.objects.get_for_model(
            StockPortfolio)
        self.stock_ct = ContentType.objects.get_for_model(Stock)

        # Set choices for account_object_id
        self.fields['account_object_id'].choices = self.get_account_choices()

        # If editing an existing instance, set initial values for the fields
        if self.instance.pk:
            self.initial['portfolio_object_id'] = StockPortfolio.objects.get(
                pk=self.instance.portfolio_object_id
            )
            self.initial['asset_object_id'] = Stock.objects.get(
                pk=self.instance.asset_object_id
            )
            if self.instance.account_object_id:
                # Set the initial value for account_object_id as "ModelName:ID"
                account_model = self.instance.account.__class__.__name__
                self.initial['account_object_id'] = f"{account_model}:{self.instance.account_object_id}"

        # Pre-set content type fields for new instances
        if not self.instance.pk:
            self.initial['portfolio_content_type'] = self.stock_portfolio_ct
            self.initial['asset_content_type'] = self.stock_ct

    def get_account_choices(self):
        Generate choices for SelfManagedAccount and ManagedAccount.
        choices = [("", "---------")]  # Blank choice for nullable field
        for account in SelfManagedAccount.objects.all():
            choices.append((f"SelfManagedAccount:{account.id}", str(account)))
        for account in ManagedAccount.objects.all():
            choices.append((f"ManagedAccount:{account.id}", str(account)))
        return choices

    def clean(self):
        cleaned_data = super().clean()

        # Ensure content types are set correctly
        cleaned_data['portfolio_content_type'] = self.stock_portfolio_ct
        cleaned_data['asset_content_type'] = self.stock_ct

        # Handle custom account_object_id
        account_choice = cleaned_data.get('account_object_id')
        if account_choice:
            try:
                model_name, account_id = account_choice.split(':')
                model_class = SelfManagedAccount if model_name == 'SelfManagedAccount' else ManagedAccount
                account = model_class.objects.get(id=account_id)
                cleaned_data['account_object_id'] = account
                cleaned_data['account_content_type'] = ContentType.objects.get_for_model(
                    model_class)
            except (ValueError, model_class.DoesNotExist):
                raise forms.ValidationError("Selected account does not exist.")
        else:
            cleaned_data['account_content_type'] = None
            cleaned_data['account_object_id'] = None

        return cleaned_data


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    form = StockHoldingAdminForm

    list_display = ['asset', 'get_portfolio', 'get_account',
                    'quantity', 'purchase_price', 'purchase_date']
    list_filter = ['portfolio_content_type',
                   'asset_content_type', 'account_content_type']
    search_fields = ['asset__name',
                     'portfolio__portfolio__profile__user__email']

    # Customize the fields displayed in the form
    fieldsets = (
        (None, {
            'fields': (
                'portfolio_object_id',
                'asset_object_id',
                'account_object_id',
                'quantity',
                'purchase_price',
                'purchase_date',
                'investment_theme',
            )
        }),
    )

    def get_portfolio(self, obj):
        Display the related StockPortfolio in the admin list view.
        if obj.base_asset_portfolio:
            return str(obj.base_asset_portfolio)
        return "-"
    get_portfolio.short_description = "Portfolio"

    def get_account(self, obj):
        Display the related Account in the admin list view.
        if obj.account:
            return str(obj.account)
        return "-"
    get_account.short_description = "Account"

    def get_queryset(self, request):
        # Optimize queryset to reduce database hits
        return super().get_queryset(request).select_related(
            'portfolio_content_type',
            'asset_content_type',
            'account_content_type',
            'investment_theme'
        ).prefetch_related('base_asset_portfolio', 'asset', 'account')

"""
@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
