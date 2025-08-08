from rest_framework import serializers
from accounts.models.stocks import StockAccount
from portfolios.models.stock import StockPortfolio
from assets.serializers.stocks import StockHoldingSerializer


class StockAccountBaseSerializer(serializers.ModelSerializer):
    active_schema_id = serializers.SerializerMethodField(read_only=True)
    active_schema_name = serializers.SerializerMethodField(read_only=True)
    current_value_profile_fx = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StockAccount
        # active_schema is computed; exclude it
        fields = [
            'id', 'name', 'broker', 'tax_status', 'account_mode', 'currency',
            'strategy', 'invested_amount', 'current_value',
            'active_schema_id', 'active_schema_name',
            'current_value_profile_fx', 'created_at', 'stock_portfolio'
        ]
        read_only_fields = [
            'id', 'active_schema_id', 'active_schema_name',
            'current_value_profile_fx', 'created_at'
        ]

    # --- derived fields ---
    def get_active_schema_id(self, obj):
        return getattr(obj.active_schema, 'id', None)

    def get_active_schema_name(self, obj):
        return getattr(obj.active_schema, 'name', None)

    def get_current_value_profile_fx(self, obj):
        # Prefer a model helper if you added it; else compute here
        try:
            val = obj.get_value_in_profile_currency()
        except AttributeError:
            # Fallback if you didn’t add get_value_in_profile_currency()
            base = obj.get_current_value() or 0
            profile_ccy = obj.stock_portfolio.portfolio.profile.currency
            from external_data.fx import get_fx_rate
            from decimal import Decimal
            fx = get_fx_rate(obj.currency, profile_ccy)
            val = (Decimal(str(base)) * Decimal(str(fx or 1))).quantize(Decimal("0.01"))
        return float(val) if val is not None else None

    # --- inputs normalization ---
    def validate_currency(self, value):
        # Allow "profile" keyword from frontend
        if isinstance(value, str) and value.lower() == "profile":
            # If stock_portfolio is in validated_data, it's not resolved yet here.
            # Pull from initial_data by ID to resolve to profile.currency.
            sp_id = self.initial_data.get("stock_portfolio")
            if not sp_id:
                raise serializers.ValidationError("stock_portfolio is required when currency='profile'.")
            try:
                sp = StockPortfolio.objects.select_related("portfolio__profile").get(pk=sp_id)
            except StockPortfolio.DoesNotExist:
                raise serializers.ValidationError("Invalid stock_portfolio.")
            return sp.portfolio.profile.currency
        return value

    def validate(self, attrs):
        mode = attrs.get('account_mode') or getattr(self.instance, 'account_mode', None)
        # For managed accounts, allow managed fields; for self-managed, null them (in create/update below)
        if mode not in {"self_managed", "managed"}:
            raise serializers.ValidationError({"account_mode": "Invalid account mode."})
        return super().validate(attrs)


class StockAccountCreateSerializer(StockAccountBaseSerializer):
    """
    Used for POST create. Accepts 'currency' as ISO code or 'profile'.
    """
    class Meta(StockAccountBaseSerializer.Meta):
        pass

    def create(self, validated_data):
        mode = validated_data.get('account_mode', 'self_managed')

        # For self-managed, scrub managed-only fields if present
        if mode == 'self_managed':
            validated_data['strategy'] = None
            validated_data['current_value'] = None
            validated_data['invested_amount'] = None

        # If currency not provided, default to profile currency (your BaseAccount.save() also does this, but explicit is nice)
        if not validated_data.get('currency'):
            sp = validated_data['stock_portfolio']
            validated_data['currency'] = sp.portfolio.profile.currency

        return super().create(validated_data)


class StockAccountUpdateSerializer(StockAccountBaseSerializer):
    """
    PATCH/PUT updates that don’t switch modes. (Mode switching should use a dedicated endpoint/service.)
    """
    class Meta(StockAccountBaseSerializer.Meta):
        read_only_fields = StockAccountBaseSerializer.Meta.read_only_fields + ['stock_portfolio', 'account_mode']

    def update(self, instance, validated_data):
        # Prevent clients from sneaking in active_schema (excluded anyway)
        validated_data.pop('active_schema', None)

        # If self-managed, strip managed-only fields
        if instance.account_mode == 'self_managed':
            validated_data.pop('strategy', None)
            validated_data.pop('current_value', None)
            validated_data.pop('invested_amount', None)

        # Normalize currency if someone PATCHes "profile"
        if 'currency' in validated_data and isinstance(validated_data['currency'], str) and validated_data['currency'].lower() == 'profile':
            sp = instance.stock_portfolio
            validated_data['currency'] = sp.portfolio.profile.currency

        return super().update(instance, validated_data)


class StockAccountDetailSerializer(StockAccountBaseSerializer):
    """
    Read serializer. Optionally include holdings for self-managed accounts.
    """
    holdings = StockHoldingSerializer(many=True, read_only=True)

    class Meta(StockAccountBaseSerializer.Meta):
        fields = StockAccountBaseSerializer.Meta.fields + ['holdings']
        read_only_fields = StockAccountBaseSerializer.Meta.read_only_fields + ['holdings']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Only include holdings if self-managed; else hide an empty list
        if instance.account_mode != 'self_managed':
            data.pop('holdings', None)
        return data

class StockAccountSwitchModeSerializer(serializers.Serializer):
    new_mode = serializers.ChoiceField(choices=[("self_managed", "Self-Managed"), ("managed", "Managed")])
    force = serializers.BooleanField(required=False, default=False)

    def save(self, **kwargs):
        account = self.context['account']
        from accounts.services.account_mode_switcher import switch_account_mode
        switch_account_mode(account, self.validated_data['new_mode'], self.validated_data['force'])
        return account