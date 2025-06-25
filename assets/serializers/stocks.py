from django.utils import timezone
from rest_framework import serializers
from external_data.fmp.dispatch import fetch_asset_data
from ..models.stocks import Stock, StockHolding


class StockHoldingCreateSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    stock = serializers.PrimaryKeyRelatedField(read_only=True)
    confirm_add = serializers.BooleanField(
        write_only=True, required=False, default=False)

    class Meta:
        model = StockHolding
        fields = ['ticker', 'stock', 'quantity', 'purchase_price',
                  'purchase_date', 'investment_theme', 'confirm_add']

    def validate_ticker(self, value):
        return value.upper()

    def validate_purchase_date(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError(
                "Purchase date cannot be in the future.")
        return value

    def _get_or_create_stock(self, ticker, confirm_add):
        stock = Stock.objects.filter(ticker=ticker).first()
        if stock:
            return stock

        if confirm_add:
            stock = Stock(ticker=ticker.upper(), is_custom=True)
            success = fetch_asset_data(stock, 'stock', verify_custom=True)
            if not success:
                raise serializers.ValidationError({
                    'ticker': f"Could not fetch or initialize data for '{ticker}"
                })
            stock.save()
            return stock

        raise serializers.ValidationError({
            'ticker': f"Stock '{ticker}' not found in database.",
            'non_field_errors': [
                "To add this as a custom stock, please confirm by setting 'confirm_add': true."
            ],
            'resubmit_data': self._build_resubmit_data(ticker)
        })

    def _build_resubmit_data(self, ticker):
        return {
            'ticker': ticker,
            'quantity': self.initial_data.get('quantity'),
            'purchase_price': self.initial_data.get('purchase_price'),
            'purchase_date': self.initial_data.get('purchase_date'),
            'investment_theme': self.initial_data.get('investment_theme'),
        }

    def create(self, validated_data):
        account = self.context['self_managed_account']
        ticker = validated_data.pop('ticker')
        confirm_add = validated_data.pop('confirm_add', False)

        stock = self._get_or_create_stock(ticker, confirm_add)

        return StockHolding.objects.create(
            stock=stock,
            self_managed_account=account,
            **validated_data
        )


class StockHoldingSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()

    class Meta:
        model = StockHolding
        fields = ['id', 'stock', 'quantity', 'purchase_price', 'purchase_date']

    def get_stock(self, obj):
        return {
            'ticker': obj.stock.ticker,
            'name': obj.stock.name
        }
