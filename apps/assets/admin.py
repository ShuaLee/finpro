# from django import forms
# from django.contrib import admin, messages
# from django.urls import reverse
# from django.utils.html import format_html
# from assets.models.base import InvestmentTheme, HoldingThemeValue
# from assets.models.stocks import Stock, StockHolding
# import logging


# logger = logging.getLogger(__name__)

# # ------------------------------ Forms ---------------------------- #


# class StockForm(forms.ModelForm):
#     class Meta:
#         model = Stock
#         fields = [
#             'ticker', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
#             'dividend_yield', 'pe_ratio', 'is_etf', 'average_volume', 'volume'
#         ]

#     def clean(self):
#         cleaned_data = super().clean()
#         ticker = cleaned_data.get('ticker')
#         is_custom = cleaned_data.get('is_custom')

#         if ticker:
#             ticker = ticker.upper()
#             cleaned_data['ticker'] = ticker
#             existing_stock = Stock.objects.filter(
#                 ticker=ticker).exclude(pk=self.instance.pk).first()
#             if existing_stock:
#                 raise forms.ValidationError(f"Ticker {ticker} already exists.")

#         return cleaned_data


# @admin.register(Stock)
# class StockAdmin(admin.ModelAdmin):
#     form = StockForm
#     list_display = ['ticker', 'name', 'is_custom',
#                     'price', 'sector', 'last_updated']
#     list_filter = ['is_custom', 'is_etf', 'sector', 'exchange']
#     search_fields = ['ticker', 'name']
#     list_per_page = 50
#     fields = [
#         'ticker', 'exchange', 'is_adr', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
#         'dividend_yield', 'pe_ratio', 'is_etf', 'average_volume', 'volume',
#         'last_updated', 'created_at'
#     ]
#     readonly_fields = ['last_updated', 'created_at']
#     actions = ['refresh_fmp_data', 'verify_custom_status']

#     def save_model(self, request, obj, form, change):
#         from external_data.fmp.dispatch import fetch_asset_data

#         if not change:  # creating new stock
#             obj.ticker = obj.ticker.upper()
#             obj.is_custom = form.cleaned_data.get('is_custom', False)

#             # Try to fetch data from FMP (even if custom)
#             success = fetch_asset_data(obj, 'stock', verify_custom=True)

#             if not success and not obj.is_custom:
#                 self.message_user(
#                     request,
#                     f"Could not fetch FMP data for {obj.ticker}.",
#                     level=messages.WARNING
#                 )
#             elif not success and obj.is_custom:
#                 self.message_user(
#                     request,
#                     f"Creating {obj.ticker} as custom stock.",
#                     level=messages.INFO
#                 )

#             try:
#                 obj.full_clean()
#                 obj.save()
#                 self.message_user(
#                     request,
#                     f"Stock {obj.ticker} created successfully.",
#                     level=messages.SUCCESS
#                 )
#             except Exception as e:
#                 self.message_user(
#                     request,
#                     f"Failed to create stock {obj.ticker}: {str(e)}",
#                     level=messages.ERROR
#                 )
#                 raise
#         else:  # updating existing
#             if not obj.is_custom:
#                 success = fetch_asset_data(obj, 'stock', verify_custom=True)
#                 if not success:
#                     self.message_user(
#                         request,
#                         f"Could not update FMP data for {obj.ticker}.",
#                         level=messages.WARNING
#                     )
#             obj.save()
#             self.message_user(
#                 request,
#                 f"Stock {obj.ticker} updated successfully.",
#                 level=messages.SUCCESS
#             )

#     def refresh_fmp_data(self, request, queryset):
#         from external_data.fmp.dispatch import fetch_asset_data

#         updated = 0
#         failed = 0

#         for stock in queryset:
#             success = fetch_asset_data(stock, 'stock', verify_custom=True)
#             if success:
#                 if stock.is_custom:
#                     stock.is_custom = False
#                     logger.info(f"Converted {stock.ticker} from custom to FMP")
#                 stock.save()
#                 updated += 1
#             else:
#                 failed += 1

#         if updated:
#             self.message_user(
#                 request,
#                 f"Successfully refreshed {updated} stock(s).",
#                 level=messages.SUCCESS
#             )
#         if failed:
#             self.message_user(
#                 request,
#                 f"Failed to refresh {failed} stock(s).",
#                 level=messages.WARNING
#             )

#     refresh_fmp_data.short_description = "Refresh FMP data for selected stocks"

#     def verify_custom_status(self, request, queryset):
#         from external_data.fmp.dispatch import fetch_asset_data
#         verified_custom = 0
#         converted_to_fmp = 0
#         failed = 0
#         for stock in queryset:
#             was_custom = stock.is_custom
#             success = fetch_asset_data(stock, 'stock', verify_custom=True)
#             if success:
#                 if was_custom:
#                     stock.is_custom = False
#                     converted_to_fmp += 1
#                     logger.info(f"Converted {stock.ticker} from custom to FMP")
#                 stock.save()
#             else:
#                 if not stock.is_custom:
#                     stock.is_custom = True
#                     stock.price = None
#                     stock.name = None
#                     stock.sector = None
#                     stock.industry = None
#                     stock.currency = None
#                     stock.dividend_yield = None
#                     stock.pe_ratio = None
#                     stock.quote_type = None
#                     stock.average_volume = None
#                     stock.volume = None
#                     stock.last_updated = None
#                     stock.save()
#                     verified_custom += 1
#                     logger.info(f"Verified {stock.ticker} as custom")
#                 else:
#                     verified_custom += 1
#             if not success and not stock.is_custom:
#                 failed += 1

#         messages_list = []
#         if converted_to_fmp:
#             messages_list.append(
#                 f"Converted {converted_to_fmp} stocks from custom to FMP.")
#         if verified_custom:
#             messages_list.append(
#                 f"Verified {verified_custom} stocks as custom.")
#         if failed:
#             messages_list.append(f"Failed to process {failed} stocks.")
#         if messages_list:
#             self.message_user(
#                 request,
#                 " ".join(messages_list),
#                 level=messages.SUCCESS if not failed else messages.WARNING
#             )

#     verify_custom_status.short_description = "Verify custom status of selected stocks"

#     def get_form(self, request, obj=None, **kwargs):
#         form = super().get_form(request, obj, **kwargs)
#         if obj and obj.is_custom:
#             for field in ['currency', 'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume']:
#                 if field in form.base_fields:
#                     form.base_fields[field].required = False
#         return form


# @admin.register(StockHolding)
# class StockHoldingAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 'asset', 'quantity', 'purchase_price', 'purchase_date',
#         'themes_display',
#     )
#     # FK/OneToOne only here:
#     list_select_related = ('stock', 'self_managed_account')

#     list_filter = (('investment_theme', admin.RelatedOnlyFieldListFilter),)
#     search_fields = ('stock__ticker', 'stock__name')  # asset__symbol likely wrong; use real FKs
#     list_editable = ['quantity', 'purchase_price', 'purchase_date']
#     list_per_page = 50

#     fields = [
#         'self_managed_account', 'stock', 'quantity', 'purchase_price',
#         'purchase_date', 'investment_theme'
#     ]
#     autocomplete_fields = ['stock', 'self_managed_account']
#     actions = ['refresh_holding_values']

#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         # IMPORTANT: prefetch M2M; select_related for FKs
#         return qs.select_related('stock', 'self_managed_account') \
#                  .prefetch_related('investment_theme', 'column_values__column')

#     @admin.display(description="Themes")
#     def themes_display(self, obj):
#         return ", ".join(obj.investment_theme.values_list('name', flat=True))

#     def get_admin_url(self, obj, model):
#         return reverse(
#             f"admin:{model._meta.app_label}_{model._meta.model_name}_change", args=[obj.id]
#         )

#     def holding_link(self, obj):
#         url = self.get_admin_url(obj, obj)
#         return format_html('<a href="{}">{}</a>', url, f"{obj.stock.ticker} ({obj.self_managed_account.name})")
#     holding_link.short_description = 'Holding'

#     def stock_link(self, obj):
#         url = self.get_admin_url(obj.stock, obj.stock)
#         return format_html('<a href="{}">{}</a>', url, obj.stock.ticker)
#     stock_link.short_description = 'Stock'

#     def self_managed_account_link(self, obj):
#         account = obj.self_managed_account
#         return format_html(
#             '<a href="{}">{}</a>',
#             self.get_admin_url(account, account),
#             account.name
#         )
#     self_managed_account_link.short_description = 'Account'

#     def current_value(self, obj):
#         return obj.get_current_value()
#     current_value.short_description = 'Current Value'

#     def refresh_holding_values(self, request, queryset):
#         updated = 0
#         for holding in queryset.select_related('stock'):
#             try:
#                 if holding.stock.fetch_fmp_data(force_update=True):
#                     holding.stock.save()
#                     updated += 1
#             except Exception as e:
#                 logger.error(f"Failed to refresh {holding.stock.ticker}: {str(e)}")
#         self.message_user(
#             request,
#             f"Refreshed {updated} holdings' stock values.",
#             level=messages.SUCCESS if updated else messages.WARNING
#         )
#     refresh_holding_values.short_description = "Refresh stock values from FMP"


# @admin.register(InvestmentTheme)
# class InvestmentThemeAdmin(admin.ModelAdmin):
#     list_display = ("id", "name", "portfolio", "parent")
#     list_filter = ("portfolio",)
#     search_fields = ("name",)
#     raw_id_fields = ("portfolio", "parent")


# @admin.register(HoldingThemeValue)
# class HoldingThemeValueAdmin(admin.ModelAdmin):
#     list_display = ("id", "holding", "theme", "value_string", "value_decimal", "value_integer")
#     list_filter = ("theme",)
#     search_fields = ("theme__name",)
#     raw_id_fields = ("theme", "holding_ct")
