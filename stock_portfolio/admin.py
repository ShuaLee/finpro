from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from .models import StockPortfolio, SelfManagedAccount, StockHolding, StockPortfolioSchema, StockPortfolioSchemaColumn, StockPortfolioSchemaColumnValue
import logging

logger = logging.getLogger(__name__)

# ------------------------------ Forms ------------------------------ #

class StockPortfolioSchemaColumnAdminForm(forms.ModelForm):
    class Meta:
        model = StockPortfolioSchemaColumn
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'source' in self.fields and 'source_field' in self.fields:
            source = (
                self.data.get('source') if self.data else
                (self.initial.get('source') or (self.instance.source if self.instance else None))
            )
            if source == 'asset':
                self.fields['source_field'].choices = [
                    ('ticker', 'Ticker'), ('price', 'Price'), ('name', 'Name')
                ]
            elif source == 'holding':
                self.fields['source_field'].choices = [
                    ('quantity', 'Quantity'), ('purchase_price', 'Purchase Price'), ('holding.ticker', 'Holding Ticker')
                ]
            elif source == 'calculated':
                self.fields['source_field'].choices = [('current_value', 'Current Value')]
            else:  # custom or None
                self.fields['source_field'].choices = [('', '---------')]

class StockPortfolioSchemaColumnValueAdminForm(forms.ModelForm):
    class Meta:
        model = StockPortfolioSchemaColumnValue
        fields = ['column', 'holding', 'value', 'is_edited']  # Explicitly include is_edited

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        column_source = None
        column_editable = True
        # Determine column source and editable status
        if 'column' in self.data:
            try:
                column_id = self.data.get('column')
                column = StockPortfolioSchemaColumn.objects.get(id=column_id)
                column_source = column.source
                column_editable = column.editable
            except (ValueError, StockPortfolioSchemaColumn.DoesNotExist):
                pass
        elif self.initial.get('column'):
            try:
                column = StockPortfolioSchemaColumn.objects.get(id=self.initial['column'])
                column_source = column.source
                column_editable = column.editable
            except StockPortfolioSchemaColumn.DoesNotExist:
                pass
        elif self.instance and hasattr(self.instance, 'column') and self.instance.column:
            column_source = self.instance.column.source
            column_editable = self.instance.column.editable
        # Apply holding-specific logic
        if column_source == 'holding':
            self.fields['value'].help_text = "Updates the StockHolding field directly (e.g., quantity, purchase_price)."
            if 'is_edited' in self.fields:
                self.fields['is_edited'].widget = forms.HiddenInput()
                self.fields['is_edited'].disabled = True
            self.fields['value'].initial = None
        # Apply non-editable logic
        if not column_editable:
            self.fields['value'].disabled = True
            self.fields['value'].help_text = "This column is not editable."
            if 'is_edited' in self.fields:
                self.fields['is_edited'].disabled = True
                self.fields['is_edited'].widget = forms.HiddenInput()

# ------------------------------ Schema ------------------------------ #

@admin.register(StockPortfolioSchema)
class StockPortfolioSchemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'stock_portfolio_link', 'created_at', 'updated_at']
    list_filter = ['stock_portfolio__portfolio__profile__user__email', 'created_at']
    search_fields = ['name', 'stock_portfolio__portfolio__profile__user__email']
    list_per_page = 50
    fields = ['name', 'stock_portfolio']
    autocomplete_fields = ['stock_portfolio']

    def stock_portfolio_link(self, obj):
        url = reverse('admin:stock_portfolio_stockportfolio_change', args=[obj.stock_portfolio.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock_portfolio)
    stock_portfolio_link.short_description = 'Stock Portfolio'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock_portfolio__portfolio__profile__user')
    
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and obj.stock_portfolio.schemas.count() <= 1:
            # Clear all messages
            storage = messages.get_messages(request)
            storage.used = True
            # Add error message
            self.message_user(
                request,
                "Cannot delete the last schema for a StockPortfolio.",
                level=messages.ERROR
            )
            # Redirect to list view
            return HttpResponseRedirect(reverse('admin:stock_portfolio_stockportfolioschema_changelist'))
        return super().delete_view(request, object_id, extra_context)

    def delete_queryset(self, request, queryset):
        blocked_schemas = [obj.name for obj in queryset if obj.stock_portfolio.schemas.count() <= 1]
        if blocked_schemas:
            storage = messages.get_messages(request)
            storage.used = True
            self.message_user(
                request,
                f"Cannot delete schema(s) {', '.join(blocked_schemas)} as they are the last schemas for their StockPortfolio.",
                level=messages.ERROR
            )
            return
        super().delete_queryset(request, queryset)

    def delete_selected(self, request, queryset):
        if request.POST.get('post'):  # Confirmation page submitted
            blocked_schemas = [obj.name for obj in queryset if obj.stock_portfolio.schemas.count() <= 1]
            if blocked_schemas:
                storage = messages.get_messages(request)
                storage.used = True
                self.message_user(
                    request,
                    f"Cannot delete schema(s) {', '.join(blocked_schemas)} as they are the last schemas for their StockPortfolio.",
                    level=messages.ERROR
                )
                return HttpResponseRedirect(reverse('admin:stock_portfolio_stockportfolioschema_changelist'))
            return super().delete_selected(request, queryset)
        # Render confirmation page for GET or initial POST
        return super().delete_selected(request, queryset)
    
@admin.register(StockPortfolioSchemaColumn)
class StockPortfolioSchemaColumnAdmin(admin.ModelAdmin):
    form = StockPortfolioSchemaColumnAdminForm
    list_display = ['title', 'schema', 'data_type', 'source', 'source_field', 'editable', 'is_deletable']
    list_filter = ['schema__stock_portfolio', 'data_type', 'source', 'is_deletable']
    search_fields = ['title', 'schema__name']
    fields = ['title', 'schema', 'data_type', 'source', 'source_field', 'formula', 'editable', 'is_deletable']
    readonly_fields = ['is_deletable']
    autocomplete_fields = ['schema']

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_deletable:
            self.message_user(
                request,
                f"Cannot delete '{obj.title}' as it is a mandatory column.",
                level=messages.ERROR
            )
            return HttpResponseRedirect(reverse('admin:stock_portfolio_stockportfolioschemacolumn_changelist'))
        return super().delete_view(request, object_id, extra_context)

    def delete_queryset(self, request, queryset):
        blocked_columns = [obj.title for obj in queryset if not obj.is_deletable]
        if blocked_columns:
            self.message_user(
                request,
                f"Cannot delete column(s) {', '.join(blocked_columns)} as they are mandatory.",
                level=messages.ERROR
            )
            return
        super().delete_queryset(request, queryset)

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.is_deletable:
            return self.readonly_fields + ['title', 'data_type', 'source', 'formula', 'editable']
        return self.readonly_fields

@admin.register(StockPortfolioSchemaColumnValue)
class StockPortfolioSchemaColumnValueAdmin(admin.ModelAdmin):
    form = StockPortfolioSchemaColumnValueAdminForm
    list_display = ['column', 'holding', 'get_value', 'is_edited']
    list_filter = ['column__schema__stock_portfolio', 'column__source', 'is_edited']
    search_fields = ['column__title', 'holding__stock__ticker']
    fields = ['column', 'holding', 'value', 'is_edited']
    readonly_fields = ['get_value']
    autocomplete_fields = ['column', 'holding']

    def get_readonly_fields(self, request, obj=None):
        if obj and (obj.column.source == 'holding' or not obj.column.editable):
            return self.readonly_fields + ['column', 'holding', 'is_edited']
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['warning'] = "Column values are automatically created when a StockHolding is added. Only edit if necessary."
        return super().add_view(request, form_url, extra_context)
# -------------------------------------------------------------------- #

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


@admin.register(StockPortfolio)
class StockPortfolioAdmin(admin.ModelAdmin):
    list_display = ['portfolio', 'created_at']
    search_fields = ['portfolio__profile__user__email']


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = [
        'holding_link', 'stock_link', 'self_managed_account_link', 'quantity', 'purchase_price',
        'purchase_date', 'current_value', 'performance', 'investment_theme'
    ]
    list_display_links = ['holding_link']
    list_filter = [
        'self_managed_account__stock_portfolio__portfolio__profile',
        'stock__quote_type', 'stock__sector', 'stock__is_adr', 'investment_theme'
    ]
    search_fields = ['stock__ticker',
                     'stock__name', 'self_managed_account__name']
    list_editable = ['quantity', 'purchase_price', 'purchase_date']
    list_per_page = 50
    fields = [
        'self_managed_account', 'stock', 'quantity', 'purchase_price',
        'purchase_date', 'investment_theme'
    ]
    autocomplete_fields = ['stock', 'self_managed_account']
    actions = ['refresh_holding_values']

    def holding_link(self, obj):
        url = reverse('admin:stock_portfolio_stockholding_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, f"{obj.stock.ticker} ({obj.self_managed_account.name})")
    holding_link.short_description = 'Holding'

    def stock_link(self, obj):
        url = reverse('admin:stocks_stock_change', args=[obj.stock.id])
        return format_html('<a href="{}">{}</a>', url, obj.stock.ticker)
    stock_link.short_description = 'Stock'

    def self_managed_account_link(self, obj):
        url = reverse('admin:stock_portfolio_selfmanagedaccount_change', args=[
                      obj.self_managed_account.id])
        return format_html('<a href="{}">{}</a>', url, obj.self_managed_account.name)
    self_managed_account_link.short_description = 'Account'

    def current_value(self, obj):
        return obj.get_current_value()
    current_value.short_description = 'Current Value'

    def performance(self, obj):
        return f"{obj.get_performance():.2f}%"
    performance.short_description = 'Performance'

    def refresh_holding_values(self, request, queryset):
        updated = 0
        for holding in queryset:
            try:
                if holding.stock.fetch_fmp_data(force_update=True):
                    holding.stock.save()
                    updated += 1
            except Exception as e:
                logger.error(
                    f"Failed to refresh {holding.stock.ticker}: {str(e)}")
        self.message_user(
            request,
            f"Refreshed {updated} holdings' stock values.",
            level='success' if updated else 'warning'
        )
    refresh_holding_values.short_description = "Refresh stock values from FMP"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stock', 'self_managed_account', 'investment_theme')
