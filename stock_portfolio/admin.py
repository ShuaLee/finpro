from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from .models import StockPortfolioSchema, StockPortfolio, StockHolding, SelfManagedAccount, ManagedAccount
from stocks.models import Stock, CustomStock

# -------------------- FORMS -------------------- #


class StockHoldingAdminForm(forms.ModelForm):
    # Custom ChoiceField for selecting Stock or CustomStock
    stock_choice = forms.ChoiceField(
        choices=(),
        label="Stock",
        required=True
    )

    # Custom ChoiceField for selecting the Account
    account_choice = forms.ChoiceField(
        choices=(),
        label="Account",
        required=False  # Account is nullable
    )

    class Meta:
        model = StockHolding
        fields = [
            'stock_choice', 'account_choice', 'quantity', 'purchase_price',
            'purchase_date', 'investment_theme'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cache content types for Stock and CustomStock
        self.stock_ct = ContentType.objects.get_for_model(Stock)
        self.custom_stock_ct = ContentType.objects.get_for_model(CustomStock)

        # Set choices for stock_choice and account_choice
        self.fields['stock_choice'].choices = self.get_stock_choices()
        self.fields['account_choice'].choices = self.get_account_choices()

        # If editing an existing instance, set initial values
        if self.instance.pk:
            # Set initial stock_choice
            if self.instance.asset_object_id and self.instance.asset:
                asset_model = self.instance.asset.__class__.__name__
                self.initial['stock_choice'] = f"{asset_model}:{self.instance.asset_object_id}"
            # Set initial account_choice
            if self.instance.account_object_id and self.instance.account:
                account_model = self.instance.account.__class__.__name__
                self.initial['account_choice'] = f"{account_model}:{self.instance.account_object_id}"

        # Pre-set asset_content_type_id for new instances to avoid model clean errors
        if not self.instance.pk:
            # Set default ContentType
            self.initial['asset_content_type'] = self.stock_ct

    def get_stock_choices(self):
        """Generate choices for Stock and CustomStock."""
        choices = []
        for stock in Stock.objects.all():
            choices.append((f"Stock:{stock.id}", str(stock)))
        for custom_stock in CustomStock.objects.all():
            choices.append(
                (f"CustomStock:{custom_stock.id}", f"[Custom] {custom_stock}"))
        return choices

    def get_account_choices(self):
        """Generate choices for SelfManagedAccount and ManagedAccount."""
        choices = [("", "---------")]  # Blank choice for nullable field
        for account in SelfManagedAccount.objects.all():
            choices.append((f"SelfManagedAccount:{account.id}", str(account)))
        for account in ManagedAccount.objects.all():
            choices.append((f"ManagedAccount:{account.id}", str(account)))
        return choices

    def clean(self):
        cleaned_data = super().clean()

        # Handle stock_choice
        stock_choice = cleaned_data.get('stock_choice')
        if stock_choice:
            try:
                model_name, stock_id = stock_choice.split(':')
                model_class = Stock if model_name == 'Stock' else CustomStock
                stock = model_class.objects.get(id=stock_id)
                cleaned_data['asset_content_type'] = ContentType.objects.get_for_model(
                    model_class)
                cleaned_data['asset_object_id'] = stock.id
            except (ValueError, model_class.DoesNotExist):
                raise forms.ValidationError(
                    {"stock_choice": "Selected stock does not exist."})
        else:
            raise forms.ValidationError({"stock_choice": "Stock is required."})

        # Handle account_choice
        account_choice = cleaned_data.get('account_choice')
        if account_choice:
            try:
                model_name, account_id = account_choice.split(':')
                model_class = SelfManagedAccount if model_name == 'SelfManagedAccount' else ManagedAccount
                account = model_class.objects.get(id=account_id)
                cleaned_data['account_content_type'] = ContentType.objects.get_for_model(
                    model_class)
                cleaned_data['account_object_id'] = account.id
            except (ValueError, model_class.DoesNotExist):
                raise forms.ValidationError(
                    {"account_choice": "Selected account does not exist."})
        else:
            cleaned_data['account_content_type'] = None
            cleaned_data['account_object_id'] = None

        # Ensure asset_content_type_id is set for model validation
        if 'asset_content_type' in cleaned_data:
            self.instance.asset_content_type = cleaned_data['asset_content_type']

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the generic foreign key fields
        instance.asset_content_type = self.cleaned_data['asset_content_type']
        instance.asset_object_id = self.cleaned_data['asset_object_id']
        instance.account_content_type = self.cleaned_data['account_content_type']
        instance.account_object_id = self.cleaned_data['account_object_id']

        if commit:
            instance.save()
            self.save_m2m()  # Save any many-to-many fields (e.g., investment_theme)
        return instance


class StockPortfolioSchemaAdminForm(forms.ModelForm):
    stock_portfolio = forms.ModelChoiceField(
        queryset=StockPortfolio.objects.all(),
        label="Stock Portfolio",
        required=True
    )

    class Meta:
        model = StockPortfolioSchema
        fields = ['stock_portfolio', 'name']

    def clean(self):
        cleaned_data = super().clean()
        stock_portfolio = cleaned_data.get('stock_portfolio')
        name = cleaned_data.get('name')
        if stock_portfolio and name:
            # Enforce unique_together constraint
            if self.instance.pk is None:  # New instance
                if StockPortfolioSchema.objects.filter(
                    stock_portfolio=stock_portfolio,
                    name=name
                ).exists():
                    raise forms.ValidationError(
                        f"A schema with name '{name}' already exists for this stock portfolio."
                    )
            else:  # Updating existing instance
                if StockPortfolioSchema.objects.filter(
                    stock_portfolio=stock_portfolio,
                    name=name
                ).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(
                        f"A schema with name '{name}' already exists for this stock portfolio."
                    )
        return cleaned_data


@admin.register(StockPortfolioSchema)
class StockPortfolioSchemaAdmin(admin.ModelAdmin):
    form = StockPortfolioSchemaAdminForm
    list_display = ['name', 'stock_portfolio', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = [
        'name', 'stock_portfolio__portfolio__profile__user__email']
    ordering = ['name']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock_portfolio')


@admin.register(SelfManagedAccount)
class SelfManagedAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_user_email', 'currency',
                    'stock_portfolio', 'account_type', 'created_at', 'last_synced')
    list_filter = ('account_type', 'created_at')
    search_fields = ('name', 'stock_portfolio__name',
                     'stock_portfolio__portfolio__profile__user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_synced')

    def get_user_email(self, obj):
        try:
            return obj.stock_portfolio.portfolio.profile.user.email
        except AttributeError:
            return "-"
    get_user_email.short_description = "User Email"
    get_user_email.admin_order_field = "stock_portfolio__portfolio__profile__user__email"


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    form = StockHoldingAdminForm

    list_display = ['asset', 'get_account',
                    'quantity', 'purchase_price', 'purchase_date']
    search_fields = ['asset__ticker']  # Updated to search by ticker

    # Customize the fields displayed in the form
    fieldsets = (
        (None, {
            'fields': (
                'stock_choice',
                'account_choice',
                'quantity',
                'purchase_price',
                'purchase_date',
                'investment_theme',
            )
        }),
    )

    def get_account(self, obj):
        """Display the related Account in the admin list view."""
        if obj.account:
            return str(obj.account)
        return "-"
    get_account.short_description = "Account"

    def get_queryset(self, request):
        # Optimize queryset to reduce database hits
        return super().get_queryset(request).select_related(
            'asset_content_type',
            'account_content_type',
            'investment_theme'
        ).prefetch_related('asset', 'account')


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
