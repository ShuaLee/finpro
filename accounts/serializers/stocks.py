from rest_framework import serializers
from accounts.models.stocks import SelfManagedAccount, ManagedAccount
from assets.serializers import StockHoldingSerializer


class SelfManagedAccountSerializer(serializers.ModelSerializer):
    holdings = StockHoldingSerializer(many=True, read_only=True)
    current_value_in_profile_fx = serializers.SerializerMethodField()
    active_schema_id = serializers.IntegerField(
        source='active_schema.id', read_only=True)
    active_schema_name = serializers.CharField(
        source='active_schema.name', read_only=True)

    class Meta:
        model = SelfManagedAccount
        fields = ['id', 'name', 'broker', 'tax_status', 'account_type',
                  'active_schema_id', 'active_schema_name', 'current_value_in_profile_fx',
                  'created_at', 'holdings']

        def get_current_value_in_profile_fx(self, obj):
            return obj.get_current_value_in_profile_fx()


class SelfManagedAccountCreateSerializer(serializers.ModelField):
    class Meta:
        model = SelfManagedAccount
        fields = ['name', 'broker', 'tax_status', 'account_type']

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stockportfolio

        # active_schema will be set automatically in model.save()
        return SelfManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )


class ManagedAccountSerializer(serializers.ModelSerializer):
    current_value_in_profile_fx = serializers.SerializerMethodField()

    class Meta:
        model = ManagedAccount
        fields = [
            'id',
            'name',
            'broker',
            'tax_status',
            'account_type',
            'strategy',
            'currency',
            'invested_amount',
            'current_value',
            'current_value_in_profile_fx',
            'created_at'
        ]

    def get_current_value_in_profile_fx(self, obj):
        return obj.get_current_value_in_profile_fx()


class ManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagedAccount
        fields = ['name', 'broker', 'tax_status', 'account_type', 'strategy',
                  'currency', 'invested_amount', 'current_value']

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        stock_portfolio = profile.portfolio.stockportfolio

        # Default to profile currency if none is provided
        validated_data.setdefault('currency', profile.currency)

        return ManagedAccount.objects.create(
            stock_portfolio=stock_portfolio,
            **validated_data
        )
