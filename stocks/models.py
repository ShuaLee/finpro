from django.conf import settings
from django.db import models
from django.utils import timezone
from portfolio.models import Asset
from .utils import parse_date, parse_decimal
import logging
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(max_length=10, unique=True)
    is_custom = models.BooleanField(default=False)

    # Company Name Data
    short_name = models.CharField(max_length=100, blank=True, null=True)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    # Price-related data
    price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # Volume
    average_volume = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Valuation
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # Company Profile
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)

    # Timestamps
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ticker

    def fetch_fmp_data(self, force_update=False):
        """
        Gets data from FMP and updates model fields.
        Returns True if fetch was successful. False if ticker is invalid. None if fetch fails.
        """
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return True

        api_key = settings.FMP_API_KEY
        quote_url = f"https://financialmodelingprep.com/api/v3/quote/{self.ticker}?apikey={api_key}"
        try:
            # Fetch quote data
            response = requests.get(quote_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"FMP quote response for {self.ticker}: {data}")

            if not data or isinstance(data, dict) and "error" in data:
                logger.warning(
                    f"Invalid ticker {self.ticker}: {data.get('error', 'No data')}")
                self.is_custom = True
                self.save(update_fields=['is_custom'])
                return False

            info = data[0]
            self.short_name = info.get('name')
            self.long_name = info.get('name')
            self.price = parse_decimal(info.get('price'))
            self.volume = info.get('volume')
            self.average_volume = info.get('avgVolume')
            self.pe_ratio = parse_decimal(info.get('pe'))
            self.last_updated = timezone.now()
            self.is_custom = False

            # Fetch profile data for sector, industry, quote_type
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
                self.is_custom = True
                self.save(update_fields=['is_custom'])
                return False
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}")
            return None

    @classmethod
    def create_from_ticker(cls, ticker):
        """
        Creates a Stock instance from a ticker and fetches FMP data.
        Sets is_custom=True for invalid tickers before saving.
        Returns the instance.
        """
        ticker = ticker.upper()
        instance = cls(ticker=ticker)  # Create without saving
        result = instance.fetch_fmp_data()
        instance.is_custom = result is False  # Set is_custom based on fetch result
        instance.save()  # Save after setting is_custom
        return instance

    @classmethod
    def bulk_update_batch(cls, stocks):
        tickers = [stock.ticker.upper() for stock in stocks]
        updated = 0
        failed = 0
        invalid = 0

        api_key = settings.FMP_API_KEY
        ticker_str = ",".join(tickers)
        url = f"https://financialmodelingprep.com/api/v3/quote/{ticker_str}?apikey={api_key}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"FMP bulk quote response for {tickers}: {data}")

            fields_to_update = [
                'short_name', 'long_name', 'price',
                'average_volume', 'volume', 'pe_ratio', 'last_updated', 'is_custom'
            ]

            invalid_stocks = []
            now = timezone.now()
            for stock in stocks:
                ticker_data = next(
                    (item for item in data if item['symbol'] == stock.ticker.upper()), None)
                if not ticker_data or 'error' in ticker_data:
                    logger.warning(
                        f"Invalid ticker {stock.ticker}: No data returned")
                    stock.is_custom = True
                    invalid_stocks.append(stock)
                    invalid += 1
                    continue

                try:
                    logger.debug(
                        f"Before update {stock.ticker}: is_custom={stock.is_custom}")
                    stock.short_name = ticker_data.get('name')
                    stock.long_name = ticker_data.get('name')
                    stock.price = parse_decimal(ticker_data.get('price'))
                    stock.volume = ticker_data.get('volume')
                    stock.average_volume = ticker_data.get('avgVolume')
                    stock.pe_ratio = parse_decimal(ticker_data.get('pe'))
                    stock.last_updated = now
                    stock.is_custom = False
                    updated += 1
                    logger.debug(
                        f"After update {stock.ticker}: is_custom={stock.is_custom}")
                except Exception as e:
                    logger.error(
                        f"Failed to process data for {stock.ticker}: {str(e)}")
                    failed += 1
                    logger.debug(
                        f"Fetch failed {stock.ticker}: is_custom={stock.is_custom} (unchanged)")

            cls.objects.bulk_update(stocks, fields_to_update)
            logger.info(
                f"Bulk update: {updated} updated, {failed} failed, {invalid} invalid.")

            for stock in invalid_stocks:
                logger.debug(
                    f"Saving invalid stock {stock.ticker}: is_custom={stock.is_custom}")
                stock.save(update_fields=['is_custom'])

            return updated, failed, invalid

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (404, 400):
                logger.warning(
                    f"Invalid tickers {tickers}: HTTP {e.response.status_code}")
                invalid_stocks = []
                for stock in stocks:
                    stock.is_custom = True
                    invalid_stocks.append(stock)
                    invalid += 1
                for stock in invalid_stocks:
                    stock.save(update_fields=['is_custom'])
                return 0, 0, invalid
            logger.error(f"Bulk fetch failed for tickers {tickers}: {str(e)}")
            return 0, len(stocks), 0
        except Exception as e:
            logger.error(f"Bulk fetch failed for tickers {tickers}: {str(e)}")
            return 0, len(stocks), 0

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)
