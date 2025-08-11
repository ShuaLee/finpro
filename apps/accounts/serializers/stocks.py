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
            'id', 'name', 'active_schema_id', 'active_schema_name',
            'current_value_in_pfx', 'created_at', 'holdings'
        ]
        read_only_fields = fields

    def get_current_value_in_pfx(self, obj):
        return obj.get_current_value_pfx()


class SelfManagedAccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelfManagedAccount
        fields = ['name']


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
