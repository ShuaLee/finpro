from core.models import Profile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils import timezone
from portfolio.models import Asset
from .utils import parse_decimal
import logging
import requests

logger = logging.getLogger(__name__)

FMP_FIELD_MAPPINGS = [
    # (model_field, api_field, source, data_type, required, default)
    ('name', 'name', 'quote', 'string', False, None),
    ('exchange', 'exchangeShortName', 'profile', 'string', False, None),
    ('is_adr', 'isAdr', 'profile', 'boolean', False, False),
    ('price', 'price', 'quote', 'decimal', True, None),
    ('volume', 'volume', 'quote', 'integer', False, None),
    ('average_volume', 'avgVolume', 'quote', 'integer', False, None),
    ('pe_ratio', 'pe', 'quote', 'decimal', False, None),
    ('sector', 'sector', 'profile', 'string', False, None),
    ('industry', 'industry', 'profile', 'string', False, None),
    ('currency', 'currency', 'profile', 'string', False, None),
    ('dividend_yield', None, 'profile', 'decimal', False, None),  # Calculated
    ('quote_type', 'quoteType', 'profile', 'string', False, 'EQUITY'),
]


class Stock(Asset):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    exchange = models.CharField(
        max_length=50, null=True, blank=True, help_text="Stock exchange (e.g., NYSE, NASDAQ)")
    is_adr = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    average_volume = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=4, blank=True, null=True)
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    is_custom = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['ticker']),
            models.Index(fields=['is_custom']),
            models.Index(fields=['exchange'])
        ]

    def __str__(self):
        return self.ticker

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)

    def get_current_value(self):
        return self.price or 0

    def _process_fmp_data(self, quote_data=None, profile_data=None):
        if self.is_custom:
            logger.info(
                f"Skipping FMP data processing for custom stock {self.ticker}")
            return True

        for model_field, _, _, _, _, default in FMP_FIELD_MAPPINGS:
            setattr(self, model_field, default)

        if quote_data:
            for model_field, api_field, source, data_type, required, _ in FMP_FIELD_MAPPINGS:
                if source == 'quote' and api_field:
                    value = quote_data.get(api_field)
                    if value is None and required:
                        logger.warning(
                            f"Missing required field {api_field} for {self.ticker}")
                        return False
                    if value is not None:
                        if data_type == 'decimal':
                            value = parse_decimal(value)
                        elif data_type == 'integer':
                            value = int(value) if value else None
                        setattr(self, model_field, value)

        if profile_data:
            for model_field, api_field, source, data_type, required, _ in FMP_FIELD_MAPPINGS:
                if source == 'profile' and api_field:
                    value = profile_data.get(api_field)
                    if value is not None:
                        if data_type == 'decimal':
                            value = parse_decimal(value)
                        elif data_type == 'integer':
                            value = int(value) if value else None
                        setattr(self, model_field, value)

            last_div = parse_decimal(profile_data.get('lastDiv'))
            if last_div and self.price:
                self.dividend_yield = (last_div * 4) / self.price
            else:
                self.dividend_yield = None

            is_fund = profile_data.get('isFund', False)
            is_etf = profile_data.get('isEtf', False)

            quote_type = profile_data.get('quoteType')
            if is_fund:
                self.quote_type = 'FUND'
            elif is_etf:
                self.quote_type = 'ETF'
            elif quote_type in ['EQUITY', 'INDEX']:
                self.quote_type = quote_type
            else:
                self.quote_type = 'EQUITY'

        self.last_updated = timezone.now()
        return True

    def fetch_fmp_data(self, force_update=False, verify_custom=False):
        if self.is_custom and not verify_custom:
            logger.info(f"Skipping FMP fetch for custom stock {self.ticker}")
            return True
        if not force_update and self.last_updated and (timezone.now() - self.last_updated).days < 1:
            logger.info(f"Using cached data for {self.ticker}")
            return True

        api_key = settings.FMP_API_KEY
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{self.ticker}?apikey={api_key}"
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{self.ticker}?apikey={api_key}"

        try:
            quote_response = requests.get(quote_url, timeout=5)
            quote_response.raise_for_status()
            quote_data = quote_response.json()
            logger.debug(f"FMP quote response for {self.ticker}: {quote_data}")

            if not quote_data or isinstance(quote_data, dict) and "error" in quote_data:
                logger.warning(f"Invalid ticker {self.ticker}")
                return False

            quote_info = quote_data[0]

            profile_data = {}
            try:
                profile_response = requests.get(profile_url, timeout=5)
                profile_response.raise_for_status()
                profile_data_list = profile_response.json()
                if profile_data_list and not isinstance(profile_data_list, dict):
                    profile_data = profile_data_list[0]
                logger.debug(
                    f"FMP profile response for {self.ticker}: {profile_data}")
            except Exception as e:
                logger.warning(
                    f"Failed to fetch profile data for {self.ticker}: {str(e)}")

            success = self._process_fmp_data(quote_info, profile_data)
            if not success:
                return False

            logger.info(f"Stock {self.ticker} updated successfully.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}")
            return False

    @classmethod
    def create_from_ticker(cls, ticker, is_custom=False):
        ticker = ticker.upper()
        existing_stock = cls.objects.filter(ticker=ticker).first()
        if existing_stock:
            logger.warning(
                f"Stock {ticker} already exists with is_custom={existing_stock.is_custom}")
            return existing_stock

        instance = cls(ticker=ticker, is_custom=is_custom)
        if is_custom:
            instance.price = 0.0
            instance.currency = 'USD'
        if not is_custom:
            success = instance.fetch_fmp_data()
            if success:
                instance.save()
                logger.info(f"Created stock {ticker} from FMP")
                return instance
            else:
                instance.is_custom = True
                logger.warning(
                    f"Ticker {ticker} not found in FMP; creating as custom")

        try:
            instance.full_clean()
            instance.save()
            return instance
        except ValidationError as e:
            logger.error(f"Failed to create stock {ticker}: {str(e)}")
            return None

    @classmethod
    def refresh_all_stocks(cls, batch_size=100, exchange=None):
        query = cls.objects.filter(is_custom=False)
        if exchange:
            query = query.filter(exchange=exchange)  # Assumes exchange field
        stocks = query

        if not stocks:
            logger.info("No stocks to refresh.")
            return 0, 0

        updated = 0
        failed = 0
        api_key = settings.FMP_API_KEY
        fields_to_update = [f for f, _, _, _, _,
                            _ in FMP_FIELD_MAPPINGS] + ['last_updated']

        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i + batch_size]
            tickers = [stock.ticker.upper() for stock in batch]
            ticker_str = ",".join(tickers)
            quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker_str}?apikey={api_key}"
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker_str}?apikey={api_key}"

            try:
                quote_response = requests.get(quote_url, timeout=10)
                quote_response.raise_for_status()
                quote_data_list = quote_response.json()

                profile_data_list = []
                try:
                    profile_response = requests.get(profile_url, timeout=10)
                    profile_response.raise_for_status()
                    profile_data_list = profile_response.json()
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch profile data for batch: {str(e)}")

                for stock in batch:
                    quote_data = next(
                        (item for item in quote_data_list if item.get(
                            'symbol') == stock.ticker.upper()), None
                    )
                    if not quote_data or 'error' in quote_data:
                        logger.warning(f"Invalid ticker {stock.ticker}")
                        failed += 1
                        continue
                    profile_data = next(
                        (item for item in profile_data_list if item.get(
                            'symbol') == stock.ticker.upper()), {}
                    )
                    if stock._process_fmp_data(quote_data, profile_data):
                        updated += 1
                    else:
                        logger.warning(f"Failed to process {stock.ticker}")
                        failed += 1

                cls.objects.bulk_update(batch, fields_to_update)

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Batch refresh failed for {tickers[:50]}...: {str(e)}")
                failed += len(batch)

        logger.info(f"Refreshed {updated} stocks, {failed} failed.")
        return updated, failed
