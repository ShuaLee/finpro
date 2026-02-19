from rest_framework import serializers

from accounts.models import Account, Holding


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = (
            "id",
            "account",
            "asset",
            "original_ticker",
            "quantity",
            "average_purchase_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "original_ticker", "created_at", "updated_at")


class AccountSerializer(serializers.ModelSerializer):
    holdings = HoldingSerializer(many=True, read_only=True)
    active_schema_id = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = (
            "id",
            "portfolio",
            "name",
            "account_type",
            "broker",
            "classification",
            "last_synced",
            "created_at",
            "active_schema_id",
            "holdings",
        )
        read_only_fields = (
            "id",
            "classification",
            "last_synced",
            "created_at",
            "active_schema_id",
        )

    def get_active_schema_id(self, obj):
        schema = obj.active_schema
        return schema.id if schema else None
