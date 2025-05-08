from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch
from django.utils import timezone
from portfolio.models import Asset, BaseAssetPortfolio
from datetime import date, datetime
from decimal import Decimal
from .constants import CURRENCY_CHOICES, SKELETON_SCHEMA, PREDEFINED_CALCULATED_COLUMNS
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# -------------------- HELPER FUNCTIONS -------------------- #


def parse_decimal(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except:
        return None


def parse_date(value):
    try:
        return datetime.fromtimestamp(value).date() if value else None
    except:
        return None


# -------------------- Cash Balances -------------------- #

class CashBalance(models.Model):
    account = models.ForeignKey(
        'SelfManagedAccount', on_delete=models.CASCADE, related_name='cash_balances')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('account', 'currency')

    def __str__(self):
        return f"{self.amount} {self.currency}"

# -------------------- STOCK PORTFOLIO -------------------- #


class StockPortfolio(BaseAssetPortfolio):
    default_self_managed_schema = models.ForeignKey(
        'Schema',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_self_managed_accounts',
    )
    default_managed_schema = models.ForeignKey(
        'Schema',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_for_managed_accounts',
    )

    def __str__(self):
        return f"Stock Portfolio for {self.portfolio.profile.user.email}"

    def clean(self):
        if self.default_self_managed_schema and self.default_self_managed_schema.stock_portfolio != self:
            raise ValidationError(
                "Default schema must belong to this portfolio.")

    def save(self, *args, **kwargs):
        if not self._state.adding and self.default_self_managed_schema is None:
            raise ValueError("default_schema must not be null after creation.")

        if self.pk:
            old = StockPortfolio.objects.get(pk=self.pk)
            old_default = old.default_self_managed_schema
        else:
            old_default = None

        super().save(*args, **kwargs)

        # Now update only accounts still using the old default
        if self.default_self_managed_schema and old_default and self.default_self_managed_schema != old_default:
            self.self_managed_accounts.filter(
                active_schema=old_default
            ).update(active_schema=self.default_self_managed_schema)

# -------------------- STOCK ACCOUNTS -------------------- #


class BaseAccount(models.Model):
    """
    Abstract class for all stock account models.
    """
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name='%(class)s_set')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        blank=True,
        help_text="Currency of the account (e.g., USD, CAD, etc.)"
    )
    broker = models.CharField(max_length=100, blank=True, null=True,
                              help_text="Brokerage platform (e.g. Robinhood, Interactive Brokers, etc.)")
    tax_status = models.CharField(
        max_length=50,
        choices=[('taxable', 'Taxable'),
                 ('tax_deferred', 'Tax-Deferred'),
                 ('tax_exempt', 'Tax-Exempt'),],
        default='taxable'
    )
    account_type = models.CharField(
        max_length=50,
        choices=[
            ('individual', 'Individual'),
            ('retirement', 'Retirement'),
            ('speculative', 'Speculative'),
            ('dividend', 'Dividend Focus'),
        ],
        default='individual',
        help_text="Purpose or strategy of the account."
    )
    last_synced = models.DateTimeField(
        null=True, blank=True, help_text="Last sync with broker.")
    use_default_schema = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Set default currency
        if not self.pk and not self.currency:
            try:
                profile = self.stock_portfolio.portfolio.profile
                self.currency = profile.currency or 'USD'
            except AttributeError:
                self.currency = 'USD'  # Fallback

        super().save(*args, **kwargs)


class SelfManagedAccount(BaseAccount):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name="self_managed_accounts")
    active_schema = models.ForeignKey(
        'Schema',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Schema used to display stock holdings for this account."
    )

    def save(self, *args, **kwargs):
        if self.use_default_schema:
            self.active_schema = self.stock_portfolio.default_self_managed_schema

        if self.active_schema and self.active_schema.stock_portfolio != self.stock_portfolio:
            raise ValidationError(
                "Selected schema does not belong to this account's stock portfolio.")

        super().save(*args, **kwargs)


class ManagedAccount(BaseAccount):
    current_value = models.DecimalField(max_digits=12, decimal_places=2)
    invested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    strategy = models.CharField(max_length=100, null=True, blank=True)
    """
    active_schema = models.ForeignKey(
        'Schema',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Schema used to display stock holdings for this account."
    )
    """

# -------------------- STOCK & STOCK HOLDING -------------------- #


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

    def fetch_yfinance_data(self, force_update=False):
        """
        Gets data from yfinance and updates model fields.
        Returns True if fetch was successful, False otherwise.
        """
        if not force_update and self.last_updated:
            time_diff = timezone.now() - self.last_updated
            if time_diff.days < 1:
                logger.info(f"Using cached data for {self.ticker}")
                return True

        try:
            ticker_obj = yf.Ticker(self.ticker)
            info = ticker_obj.info

            if not isinstance(info, dict) or 'symbol' not in info:
                logger.warning(
                    f"Invalid or missing data for {self.ticker}: {info}")
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

            self.fifty_two_week_high = parse_decimal(
                info.get('fiftyTwoWeekHigh'))
            self.fifty_two_week_low = parse_decimal(
                info.get('fiftyTwoWeekLow'))

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
            self.save()

            logger.info(f"Stock {self.ticker} updated successfully.")
            return True

        except Exception as e:
            logger.error(
                f"Failed to fetch data for {self.ticker}: {e}", exc_info=False)
            return False

    @classmethod
    def create_from_ticker(cls, ticker):
        """
        Creates a Stock instance from a ticker and fetches yfinance data.
        Returns the instance if successful, None otherwise.
        """
        ticker = ticker.upper()
        instance = cls(ticker=ticker)

        if instance.fetch_yfinance_data():
            instance.is_custom = not any([
                instance.short_name,
                instance.long_name,
                instance.exchange
            ])
            instance.save()
            return instance
        else:
            instance.is_custom = True
            logger.warning(
                f"Stock creation failed for {ticker}: No data fetched")

        instance.save()
        return instance

    def save(self, *args, **kwargs):
        if self.ticker:
            self.ticker = self.ticker.upper()
        # Prevent redundant fetch during save
        super().save(*args, **kwargs)


class StockHolding(models.Model):
    stock_account = models.ForeignKey(
        SelfManagedAccount, on_delete=models.CASCADE, related_name='stockholdings')
    stock = models.ForeignKey(Stock, null=True, on_delete=models.SET_NULL)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    purchase_price = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('stock_account', 'stock')

    def __str__(self):
        return f"{self.stock} ({self.shares} shares)"

    def save(self, *args, **kwargs):
        logger.debug(f"Saving StockHolding {self.id}, shares={self.shares}")
        super().save(*args, **kwargs)
        return self

# -------------------- SCHEMA -------------------- #


class Schema(models.Model):
    stock_portfolio = models.ForeignKey(
        StockPortfolio, on_delete=models.CASCADE, related_name="schemas")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stock_portfolio', 'name')
        verbose_name_plural = "Schemas"

    def __str__(self):
        return self.name

    def get_structured_holdings(self, account):
        schema_columns = list(self.columns.all())
        holdings = account.stockholdings.select_related(
            'stock').prefetch_related('column_values')

        columns = [
            {
                "id": col.id,
                "name": col.name,
                "data_type": col.data_type,
                "source": col.source,
                "source_field": col.source_field
            }
            for col in schema_columns
        ]

        rows = []
        for holding in holdings:
            row_values = []
            for col in schema_columns:
                value_obj = holding.column_values.filter(column=col).first()
                if not value_obj:
                    value_obj, created = SchemaColumnValue.objects.get_or_create(
                        stock_holding=holding,
                        column=col,
                        defaults={"value": None}
                    )
                    if created:
                        if col.source == 'stock':
                            value_obj.value = str(
                                getattr(holding.stock, col.source_field, None))
                        elif col.source == 'holding':
                            value_obj.value = str(
                                getattr(holding, col.source_field, None))
                        value_obj.save()
                row_values.append({
                    "column_id": col.id,
                    "value_id": value_obj.id,
                    "value": value_obj.value,
                    "is_edited": value_obj.is_edited if col.source == 'stock' else False
                })
            rows.append({
                "holding_id": holding.id,
                "values": row_values
            })

        return {
            "columns": columns,
            "rows": rows
        }

    def delete(self, *args, **kwargs):
        schemas = Schema.objects.filter(stock_portfolio=self.stock_portfolio)
        if schemas.count() <= 1:
            raise ValidationError("Cannot delete the last remaining schema.")

        if self == self.stock_portfolio.default_schema:
            fallback = schemas.exclude(id=self.id).first()
            if fallback:
                self.stock_portfolio.default_schema = fallback
                self.stock_portfolio.save(update_fields=["default_schema"])

        super().delete(*args, **kwargs)


class SchemaColumn(models.Model):
    DATA_TYPES = [
        ('decimal', 'Number'),
        ('string', 'String'),
        ('date', 'Date'),
        ('url', 'URL'),
    ]
    SOURCE_TYPE = [
        ('stock', 'Stock'),
        ('holding', 'StockHolding'),
        ('calculated', 'Calculated'),
        ('custom', 'Custom'),
    ]

    schema = models.ForeignKey(
        Schema, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=10, choices=DATA_TYPES)
    source = models.CharField(max_length=20, choices=SOURCE_TYPE)
    source_field = models.CharField(max_length=100, blank=True, null=True)
    formula = models.TextField(blank=True, null=True)
    editable = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return f"{self.name} ({self.source})"


class SchemaColumnValue(models.Model):
    stock_holding = models.ForeignKey(
        StockHolding, on_delete=models.CASCADE, related_name='column_values')
    column = models.ForeignKey(
        SchemaColumn, on_delete=models.CASCADE, related_name='values')
    value = models.TextField(blank=True, null=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        unique_together = ('stock_holding', 'column')

    def __str__(self):
        return f"{self.stock_holding} | {self.column.name} = {self.value}"

    def validate_value(self, value):
        """Validate that the value matches the column's data type."""
        if value is None:
            return
        data_type = self.column.data_type
        try:
            if data_type == 'decimal':
                # Convert to Decimal, strip whitespace
                decimal_value = Decimal(str(value).strip())
                if self.column.source == 'holding' and self.column.source_field == 'shares':
                    # Match StockHolding.shares constraints (max_digits=15, decimal_places=4)
                    decimal_value = decimal_value.quantize(
                        Decimal('0.0001'), rounding='ROUND_HALF_UP')
                    # Check total digits (11 before decimal + 4 after = 15)
                    if len(str(abs(decimal_value).quantize(Decimal('1'))).split('.')[0]) > 11:
                        raise ValueError("Too many digits for shares")
                return decimal_value
            elif data_type == 'date':
                datetime.strptime(value, '%Y-%m-%d')
            elif data_type == 'url':
                from django.core.validators import URLValidator
                URLValidator()(value)
            # 'string' type needs no validation
        except (ValueError, TypeError, ValidationError) as e:
            logger.error(
                f"Validation failed for value '{value}' (data_type={data_type}): {str(e)}")
            raise ValidationError(
                f"Invalid value for {self.column.source_field or 'value'}: {value}"
            )
        return value

    def reset_to_default(self):
        """Reset the value to the default from stock or holding without updating StockHolding."""
        if self.column.source == 'stock':
            default_value = getattr(
                self.stock_holding.stock, self.column.source_field, None)
            self.is_edited = False
        elif self.column.source == 'holding':
            default_value = getattr(
                self.stock_holding, self.column.source_field, None)
            self.is_edited = False  # Not used for holding, but set to False for consistency
        else:
            default_value = None
            self.is_edited = False

        self.value = str(default_value) if default_value is not None else None
        super().save()
        logger.debug(
            f"Reset SchemaColumnValue {self.id}, value={self.value}, is_edited={self.is_edited}")

    def save(self, *args, **kwargs):
        # Validate the value if it's being set manually
        if 'value' in kwargs.get('update_fields', []) or not self.pk:
            validated_value = self.validate_value(self.value)
            if self.column.data_type == 'decimal':
                self.value = str(validated_value)  # Store as string

        super().save(*args, **kwargs)
        logger.debug(
            f"Saved SchemaColumnValue {self.id}, value={self.value}, is_edited={self.is_edited}")
