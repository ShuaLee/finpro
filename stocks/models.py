from django.db import models
from django.utils import timezone
from portfolio.models import Asset
from retrying import retry
from .utils import parse_date, parse_decimal
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)

"""
class Stock(Asset):
    id = models.AutoField(primary_key=True)
    ticker = models.CharField(max_length=10, unique=True)
    is_custom = models.BooleanField(default=False)

    # Stock data
    short_name = models.CharField(max_length=100, blank=True, null=True)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    quote_type = models.CharField(max_length=50, blank=True, null=True)
    market = models.CharField(max_length=50, blank=True, null=True)

    # Price-related data
    last_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    previous_close = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    open_price = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    day_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    day_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # 52-week range
    fifty_two_week_high = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)
    fifty_two_week_low = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True)

    # Volume
    average_volume = models.BigIntegerField(null=True, blank=True)
    average_volume_10d = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Valuation
    market_cap = models.BigIntegerField(null=True, blank=True)
    beta = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    forward_pe = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    price_to_book = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)

    # Dividends
    dividend_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    dividend_yield = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    payout_ratio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField(null=True, blank=True)

    # Company Profile
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    full_time_employees = models.IntegerField(null=True, blank=True)
    long_business_summary = models.TextField(null=True, blank=True)

    # Timestamps
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.ticker

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _fetch_yfinance_info(self):
        return yf.Ticker(self.ticker).info

    def fetch_yfinance_data(self, force_update=False):
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return True

        try:
            info = self._fetch_yfinance_info()

            if not isinstance(info, dict) or 'symbol' not in info:
                logger.warning(f"Invalid ticker {self.ticker}: {info}")
                self.is_custom = True
                self.save(update_fields=['is_custom'])
                return False

            self.short_name = info.get('shortName')
            self.long_name = info.get('longName')
            self.currency = info.get('currency')
            self.exchange = info.get('exchange')
            self.quote_type = info.get('quoteType')
            self.market = info.get('market')

            self.last_price = parse_decimal(info.get('currentPrice') or info.get(
                'regularMarketPrice') or info.get('previousClose'))
            self.previous_close = parse_decimal(info.get('previousClose'))
            self.open_price = parse_decimal(info.get('open'))
            self.day_high = parse_decimal(info.get('dayHigh'))
            self.day_low = parse_decimal(info.get('dayLow'))

            self.fifty_two_week_high = parse_decimal(info.get('fiftyTwoWeekHigh'))
            self.fifty_two_week_low = parse_decimal(info.get('fiftyTwoWeekLow'))

            self.average_volume = info.get('averageVolume')
            self.average_volume_10d = info.get('averageDailyVolume10Day')
            self.volume = info.get('volume')

            self.market_cap = info.get('marketCap')
            self.beta = parse_decimal(info.get('beta'))
            self.pe_ratio = parse_decimal(info.get('trailingPE'))
            self.forward_pe = parse_decimal(info.get('forwardPE'))
            self.price_to_book = parse_decimal(info.get('priceToBook'))

            self.dividend_rate = parse_decimal(info.get('dividendRate'))
            self.dividend_yield = parse_decimal(info.get('dividendYield'))
            self.payout_ratio = parse_decimal(info.get('payoutRatio'))
            self.ex_dividend_date = parse_date(info.get('exDividendDate'))

            self.sector = info.get('sector')
            self.industry = info.get('industry')
            self.website = info.get('website')
            self.full_time_employees = info.get('fullTimeEmployees')
            self.long_business_summary = info.get('longBusinessSummary')

            self.last_updated = timezone.now()
            self.is_custom = False
            self.save()

            logger.info(f"Stock {self.ticker} updated successfully.")
            return True

        except Exception as e:
            logger.error(f"Failed to fetch data for {self.ticker}: {str(e)}", exc_info=True)
            return None

    @classmethod
    def create_from_ticker(cls, ticker):
        ticker = ticker.upper()
        instance = cls(ticker=ticker)
        result = instance.fetch_yfinance_data()
        instance.is_custom = result is False  # True only for invalid tickers
        instance.save()
        return instance

    @classmethod
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def _fetch_tickers_info(cls, tickers):
        return yf.Tickers(' '.join(tickers))

    @classmethod
    def bulk_update_from_yfinance(cls, stocks):
        tickers = [stock.ticker.upper() for stock in stocks]
        updated = 0
        failed = 0
        invalid = 0

        try:
            tickers_obj = cls._fetch_tickers_info(tickers)
            now = timezone.now()

            fields_to_update = [
                'short_name', 'long_name', 'currency', 'exchange', 'quote_type', 'market',
                'last_price', 'previous_close', 'open_price', 'day_high', 'day_low',
                'fifty_two_week_high', 'fifty_two_week_low',
                'average_volume', 'average_volume_10d', 'volume',
                'market_cap', 'beta', 'pe_ratio', 'forward_pe', 'price_to_book',
                'dividend_rate', 'dividend_yield', 'payout_ratio', 'ex_dividend_date',
                'sector', 'industry', 'website', 'full_time_employees', 'long_business_summary',
                'last_updated', 'is_custom'
            ]

            invalid_stocks = []
            for stock in stocks:
                try:
                    logger.debug(f"Before update {stock.ticker}: is_custom={stock.is_custom}")
                    info = tickers_obj.tickers.get(stock.ticker.upper()).info
                    if not isinstance(info, dict) or 'symbol' not in info:
                        logger.warning(f"Invalid ticker {stock.ticker}: {info}")
                        stock.is_custom = True
                        invalid_stocks.append(stock)
                        invalid += 1
                        continue

                    stock.short_name = info.get('shortName')
                    stock.long_name = info.get('longName')
                    stock.currency = info.get('currency')
                    stock.exchange = info.get('exchange')
                    stock.quote_type = info.get('quoteType')
                    stock.market = info.get('market')

                    stock.last_price = parse_decimal(info.get('currentPrice') or info.get(
                        'regularMarketPrice') or info.get('previousClose'))
                    stock.previous_close = parse_decimal(info.get('previousClose'))
                    stock.open_price = parse_decimal(info.get('open'))
                    stock.day_high = parse_decimal(info.get('dayHigh'))
                    stock.day_low = parse_decimal(info.get('dayLow'))

                    stock.fifty_two_week_high = parse_decimal(info.get('fiftyTwoWeekHigh'))
                    stock.fifty_two_week_low = parse_decimal(info.get('fiftyTwoWeekLow'))

                    stock.average_volume = info.get('averageVolume')
                    stock.average_volume_10d = info.get('averageDailyVolume10Day')
                    stock.volume = info.get('volume')

                    stock.market_cap = info.get('marketCap')
                    stock.beta = parse_decimal(info.get('beta'))
                    stock.pe_ratio = parse_decimal(info.get('trailingPE'))
                    stock.forward_pe = parse_decimal(info.get('forwardPE'))
                    stock.price_to_book = parse_decimal(info.get('priceToBook'))

                    stock.dividend_rate = parse_decimal(info.get('dividendRate'))
                    stock.dividend_yield = parse_decimal(info.get('dividendYield'))
                    stock.payout_ratio = parse_decimal(info.get('payoutRatio'))
                    stock.ex_dividend_date = parse_date(info.get('exDividendDate'))

                    stock.sector = info.get('sector')
                    stock.industry = info.get('industry')
                    stock.website = info.get('website')
                    stock.full_time_employees = info.get('fullTimeEmployees')
                    stock.long_business_summary = info.get('longBusinessSummary')

                    stock.last_updated = now
                    stock.is_custom = False
                    updated += 1
                    logger.debug(f"After update {stock.ticker}: is_custom={stock.is_custom}")

                except Exception as e:
                    logger.error(f"Failed to fetch data for {stock.ticker}: {str(e)}", exc_info=True)
                    failed += 1
                    logger.debug(f"Fetch failed {stock.ticker}: is_custom={stock.is_custom} (unchanged)")

            cls.objects.bulk_update(stocks, fields_to_update)
            logger.info(f"Bulk update: {updated} updated, {failed} failed, {invalid} invalid.")

            # Explicitly save invalid stocks' is_custom
            for stock in invalid_stocks:
                logger.debug(f"Saving invalid stock {stock.ticker}: is_custom={stock.is_custom}")
                stock.save(update_fields=['is_custom'])

            return updated, failed, invalid

        except Exception as e:
            logger.error(f"Bulk fetch failed for tickers {tickers}: {str(e)}", exc_info=True)
            return 0, len(stocks), 0

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)
"""