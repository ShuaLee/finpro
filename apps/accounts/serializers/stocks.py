from rest_framework import serializers
from accounts.models import SelfManagedAccount, ManagedAccount
from assets.serializers.stocks import StockHoldingSerializer


# -----------------------------
# SelfManagedAccount
# -----------------------------
class SelfManagedAccountSerializer(serializers.ModelSerializer):
    holdings = StockHoldingSerializer(many=True, read_only=True)
    current_value_in_pfx = serializers.SerializerMethodField()
    active_schema_id = serializers.IntegerField(
        source='active_schema.id', read_only=True)
    active_schema_name = serializers.CharField(
        source='active_schema.name', read_only=True)

    class Meta:
        model = SelfManagedAccount
        fields = [
            'id', 'name', 'broker', 'tax_status', 'account_type',
            'active_schema_id', 'active_schema_name',
            'current_value_in_pfx', 'created_at', 'holdings'
        ]
        read_only_fields = [
            'id', 'active_schema_id', 'active_schema_name',
            'created_at', 'holdings', 'current_value_in_pfx'
        ]

    def get_current_value_in_pfx(self, obj):
        return obj.get_current_value_pfx()


class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    broker = serializers.CharField(
        required=False, allow_null=True, allow_blank=True)

    tax_status = serializers.ChoiceField(
        choices=SelfManagedAccount._meta.get_field('tax_status').choices
    )
    account_type = serializers.ChoiceField(
        choices=SelfManagedAccount._meta.get_field('account_type').choices
    )

    class Meta:
        model = SelfManagedAccount
        fields = ['name', 'broker', 'tax_status', 'account_type']


# -----------------------------
# ManagedAccount
# -----------------------------
class ManagedAccountSerializer(serializers.ModelSerializer):
    current_value_in_profile_fx = serializers.SerializerMethodField()
    active_schema_id = serializers.IntegerField(
        source='active_schema.id', read_only=True)
    active_schema_name = serializers.CharField(
        source='active_schema.name', read_only=True)

    class Meta:
        model = ManagedAccount
        fields = [
            'id', 'name', 'broker', 'tax_status', 'account_type',
            'strategy', 'currency', 'invested_amount', 'current_value',
            'current_value_in_profile_fx', 'active_schema_id', 'active_schema_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'current_value_in_profile_fx',
            'active_schema_id', 'active_schema_name', 'created_at'
        ]

    def get_current_value_in_profile_fx(self, obj):
        return obj.get_current_value_in_pfx()


class ManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagedAccount
        fields = [
            'name', 'broker', 'tax_status', 'account_type',
            'strategy', 'currency', 'invested_amount', 'current_value'
        ]
