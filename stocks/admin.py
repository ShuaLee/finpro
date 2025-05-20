from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin, messages
from .models import Stock
import logging

logger = logging.getLogger(__name__)


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'ticker', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
            'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume'
        ]

    def clean(self):
        cleaned_data = super().clean()
        ticker = cleaned_data.get('ticker')
        is_custom = cleaned_data.get('is_custom')

        if ticker:
            ticker = ticker.upper()
            cleaned_data['ticker'] = ticker
            existing_stock = Stock.objects.filter(
                ticker=ticker).exclude(pk=self.instance.pk).first()
            if existing_stock:
                raise forms.ValidationError(f"Ticker {ticker} already exists.")

        return cleaned_data


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    form = StockForm
    list_display = ['ticker', 'name', 'is_custom',
                    'price', 'sector', 'last_updated']
    list_filter = ['is_custom', 'quote_type', 'sector']
    search_fields = ['ticker', 'name']
    list_per_page = 50
    fields = [
        'ticker', 'is_custom', 'price', 'name', 'currency', 'sector', 'industry',
        'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume',
        'last_updated', 'created_at'
    ]
    readonly_fields = ['last_updated', 'created_at']
    actions = ['refresh_fmp_data', 'verify_custom_status']

    def save_model(self, request, obj, form, change):
        is_custom = form.cleaned_data.get('is_custom', False)
        if not change:
            stock = Stock.create_from_ticker(obj.ticker, is_custom=is_custom)
            if not stock:
                self.message_user(
                    request,
                    f"Failed to create stock {obj.ticker}: Validation error.",
                    level=messages.ERROR
                )
                raise ValidationError(f"Failed to create stock {obj.ticker}")
            obj.pk = stock.pk
            obj.__dict__.update(stock.__dict__)
            self.message_user(
                request,
                f"Stock {obj.ticker} created {'as custom' if stock.is_custom else 'from FMP'}.",
                level=messages.SUCCESS
            )
        else:
            if not obj.is_custom:
                success = obj.fetch_fmp_data(force_update=True)
                if not success:
                    self.message_user(
                        request,
                        f"Failed to refresh FMP data for {obj.ticker}.",
                        level=messages.WARNING
                    )
            obj.save()
            self.message_user(
                request,
                f"Stock {obj.ticker} updated successfully.",
                level=messages.SUCCESS
            )

    def refresh_fmp_data(self, request, queryset):
        updated = 0
        failed = 0
        for stock in queryset:
            success = stock.fetch_fmp_data(
                force_update=True, verify_custom=True)
            if success:
                if stock.is_custom:
                    stock.is_custom = False
                    logger.info(f"Converted {stock.ticker} from custom to FMP")
                stock.save()
                updated += 1
            else:
                failed += 1
        if updated:
            self.message_user(
                request, f"Successfully updated {updated} stocks.", level=messages.SUCCESS)
        if failed:
            self.message_user(
                request, f"Failed to update {failed} stocks.", level=messages.WARNING)

    refresh_fmp_data.short_description = "Refresh FMP data for selected stocks"

    def verify_custom_status(self, request, queryset):
        verified_custom = 0
        converted_to_fmp = 0
        failed = 0
        for stock in queryset:
            was_custom = stock.is_custom
            success = stock.fetch_fmp_data(
                force_update=True, verify_custom=True)
            if success:
                if was_custom:
                    stock.is_custom = False
                    converted_to_fmp += 1
                    logger.info(f"Converted {stock.ticker} from custom to FMP")
                stock.save()
            else:
                if not stock.is_custom:
                    stock.is_custom = True
                    stock.price = None
                    stock.name = None
                    stock.sector = None
                    stock.industry = None
                    stock.currency = None
                    stock.dividend_yield = None
                    stock.pe_ratio = None
                    stock.quote_type = None
                    stock.average_volume = None
                    stock.volume = None
                    stock.last_updated = None
                    stock.save()
                    verified_custom += 1
                    logger.info(f"Verified {stock.ticker} as custom")
                else:
                    verified_custom += 1
            if not success and not stock.is_custom:
                failed += 1

        messages_list = []
        if converted_to_fmp:
            messages_list.append(
                f"Converted {converted_to_fmp} stocks from custom to FMP.")
        if verified_custom:
            messages_list.append(
                f"Verified {verified_custom} stocks as custom.")
        if failed:
            messages_list.append(f"Failed to process {failed} stocks.")
        if messages_list:
            self.message_user(
                request,
                " ".join(messages_list),
                level=messages.SUCCESS if not failed else messages.WARNING
            )

    verify_custom_status.short_description = "Verify custom status of selected stocks"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.is_custom:
            for field in ['currency', 'dividend_yield', 'pe_ratio', 'quote_type', 'average_volume', 'volume']:
                form.base_fields[field].required = False
        return form
