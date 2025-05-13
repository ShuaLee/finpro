from django.conf import settings
from django.db import models
from django.utils import timezone
from portfolio.models import Asset
from .utils import parse_date, parse_decimal
import logging
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


class BaseStock(Asset):
    ticker = models.CharField(max_length=10, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.ticker

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)


class Stock(BaseStock):
    # Company Name Data
    name = models.CharField(max_length=200, blank=True, null=True)

    # Price-related data
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, null=True)

    # Volume
    average_volume = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Dividend
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=4, blank=True, null=True)

    # Valuation
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # Company Profile
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    # Timestamps
    last_updated = models.DateTimeField(null=True, blank=True)

    def fetch_fmp_data(self, force_update=False):
        if not force_update and self.last_updated and (timezone.now() - self.last_updated).days < 1:
            logger.info(f"Using cached data for {self.ticker}")
            return True

        api_key = settings.FMP_API_KEY
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{self.ticker}?apikey={api_key}"

        try:
            response = requests.get(quote_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"FMP quote response for {self.ticker}: {data}")

            if not data or isinstance(data, dict) and "error" in data:
                logger.warning(f"Invalid ticker {self.ticker}")
                return False

            info = data[0]
            self.name = info.get('name')
            self.price = parse_decimal(info.get('price'))
            self.volume = info.get('volume')
            self.average_volume = info.get('avgVolume')
            self.pe_ratio = parse_decimal(info.get('pe'))
            self.last_updated = timezone.now()

            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{self.ticker}?apikey={api_key}"

            try:
                profile_response = requests.get(profile_url, timeout=5)
                profile_response.raise_for_status()
                profile_data = profile_response.json()
                logger.debug(
                    f"FMP profile response for {self.ticker}: {profile_data}")
                if profile_data and not isinstance(profile_data, dict):
                    profile_info = profile_data[0]
                    self.sector = profile_info.get('sector')
                    self.industry = profile_info.get('industry')
                    self.currency = profile_info.get('currency')
                    last_div = parse_decimal(profile_info.get('lastDiv'))
                    if last_div and self.price:
                        self.dividend_yield = (last_div * 4) / self.price
                        logger.info(
                            f"Calculated dividend_yield for {self.ticker}: {self.dividend_yield}")
                    else:
                        self.dividend_yield = None
                        logger.warning(
                            f"No lastDiv or price for {self.ticker}, dividend_yield set to None")

                    # Set quote_type based on quoteType or isEtf
                    quote_type = profile_info.get('quoteType')
                    is_etf = profile_info.get('isEtf', False)
                    if quote_type in ['EQUITY', 'ETF', 'MUTUAL FUND', 'INDEX']:
                        self.quote_type = quote_type
                    elif is_etf:
                        self.quote_type = 'ETF'
                    else:
                        self.quote_type = 'EQUITY'  # Default for stocks
                    if not quote_type:
                        logger.warning(
                            f"Missing quoteType for {self.ticker}, using {self.quote_type}")
            except Exception as e:
                logger.warning(
                    f"Failed to fetch profile data for {self.ticker}: {str(e)}")
                self.quote_type = 'EQUITY'  # Fallback if profile fetch fails

            self.save()
            logger.info(f"Stock {self.ticker} updated successfully.")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (404, 400):
                logger.warning(
                    f"Invalid ticker {self.ticker}: HTTP {e.response.status_code}")
                return False
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}")
            return None

    @classmethod
    def create_from_ticker(cls, ticker):
        ticker = ticker.upper()
        instance = cls(ticker=ticker)
        result = instance.fetch_fmp_data()
        if result is False:
            logger.info(f"Ticker {ticker} not found in FMP.")
            return None
        instance.save()
        return instance

    @classmethod
    def bulk_update_from_fmp(cls, batch_size=100, stocks=None):
        stocks = stocks if stocks is not None else cls.objects.exclude(
            ticker__endswith='.AX')
        if not stocks:
            logger.info("No stocks to update.")
            return 0, 0, 0
        updated = 0
        failed = 0
        invalid = 0
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i + batch_size]
            u, f, inv = cls._bulk_update_batch(batch)
            updated += u
            failed += f
            invalid += inv
        logger.info(
            f"Total: {updated} updated, {failed} failed, {invalid} invalid.")
        return updated, failed, invalid

    @classmethod
    def _bulk_update_batch(cls, stocks):
        tickers = [stock.ticker.upper() for stock in stocks]
        updated = 0
        failed = 0
        invalid = 0
        api_key = settings.FMP_API_KEY
        ticker_str = ",".join(tickers)
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{ticker_str}?apikey={api_key}"
        try:
            response = requests.get(quote_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"FMP quote response for {tickers}: {data}")

            fields_to_update = [
                'name', 'price', 'average_volume', 'volume',
                'pe_ratio', 'sector', 'industry', 'currency', 'dividend_yield', 'quote_type',
                'last_updated'
            ]

            for stock in stocks:
                ticker_data = next(
                    (item for item in data if item['symbol'] == stock.ticker.upper()), None)
                if not ticker_data or 'error' in ticker_data:
                    logger.warning(
                        f"Invalid ticker {stock.ticker} - possible ticker change, please review")
                    InvalidTicker.objects.get_or_create(
                        ticker=stock.ticker, defaults={'resolved': False})
                    invalid += 1
                    continue

                try:
                    stock.name = ticker_data.get('name')
                    stock.price = parse_decimal(ticker_data.get('price'))
                    stock.volume = ticker_data.get('volume')
                    stock.average_volume = ticker_data.get('avgVolume')
                    stock.pe_ratio = parse_decimal(ticker_data.get('pe'))

                    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{stock.ticker}?apikey={api_key}"
                    profile_response = requests.get(profile_url, timeout=5)
                    profile_response.raise_for_status()
                    profile_data = profile_response.json()
                    logger.debug(
                        f"FMP profile response for {stock.ticker}: {profile_data}")

                    if profile_data and not isinstance(profile_data, dict):
                        profile_info = profile_data[0]
                        stock.sector = profile_info.get('sector')
                        stock.industry = profile_info.get('industry')
                        stock.currency = profile_info.get('currency')
                        stock.quote_type = profile_info.get(
                            'quoteType', 'EQUITY')
                        if stock.quote_type not in ['EQUITY', 'ETF', 'MUTUAL FUND', 'INDEX']:
                            stock.quote_type = 'EQUITY'
                            logger.warning(
                                f"Invalid quoteType for {stock.ticker}, using EQUITY")
                        if not stock.quote_type:
                            logger.warning(
                                f"Missing quoteType for {stock.ticker}, using EQUITY")
                            stock.quote_type = 'EQUITY'

                        last_div = parse_decimal(profile_info.get('lastDiv'))
                        if last_div and stock.price:
                            stock.dividend_yield = (last_div * 4) / stock.price
                            logger.info(
                                f"Calculated dividend_yield for {stock.ticker}: {stock.dividend_yield}")
                        else:
                            stock.dividend_yield = None
                            logger.warning(
                                f"No lastDiv or price for {stock.ticker}, dividend_yield set to None")

                    stock.last_updated = timezone.now()
                    updated += 1
                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"Failed to fetch data for {stock.ticker}: {str(e)}")
                    failed += 1
                    continue
                except Exception as e:
                    logger.error(
                        f"Failed to process data for {stock.ticker}: {str(e)}")
                    failed += 1
                    continue

            cls.objects.bulk_update(stocks, fields_to_update)
            logger.info(
                f"Batch update: {updated} updated, {failed} failed, {invalid} invalid.")
            return updated, failed, invalid

        except requests.exceptions.RequestException as e:
            logger.error(f"Bulk fetch failed for {tickers}: {str(e)}")
            return 0, len(stocks), 0


class CustomStock(BaseStock):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class InvalidTicker(models.Model):
    ticker = models.CharField(max_length=10)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('ticker', 'detected_at')

    def __str__(self):
        return f"{self.ticker} (Detected: {self.detected_at})"
