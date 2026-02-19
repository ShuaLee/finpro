from rest_framework import serializers

from accounts.models import (
    Account,
    AccountTransaction,
    AccountType,
    BrokerageConnection,
    Holding,
    HoldingSnapshot,
    ReconciliationIssue,
    AccountJob,
)
from assets.models.core import AssetType


class AccountTypeSerializer(serializers.ModelSerializer):
    allowed_asset_type_slugs = serializers.SerializerMethodField()

    class Meta:
        model = AccountType
        fields = (
            "id",
            "name",
            "slug",
            "is_system",
            "description",
            "allowed_asset_type_slugs",
        )

    def get_allowed_asset_type_slugs(self, obj):
        return list(obj.allowed_asset_types.values_list("slug", flat=True))


class CustomAccountTypeCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allowed_asset_type_slugs = serializers.ListField(
        child=serializers.SlugField(),
        allow_empty=False,
    )

    def validate_allowed_asset_type_slugs(self, value):
        slugs = [slug.strip().lower() for slug in value]
        asset_types = list(AssetType.objects.filter(slug__in=slugs))
        if len(asset_types) != len(set(slugs)):
            raise serializers.ValidationError("One or more asset types are invalid.")
        return slugs


class HoldingSerializer(serializers.ModelSerializer):
    asset_display_name = serializers.CharField(source="asset.display_name", read_only=True)
    asset_type = serializers.CharField(source="asset.asset_type.slug", read_only=True)

    class Meta:
        model = Holding
        fields = (
            "id",
            "account",
            "asset",
            "asset_type",
            "asset_display_name",
            "original_ticker",
            "quantity",
            "average_purchase_price",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "account",
            "asset",
            "asset_type",
            "asset_display_name",
            "original_ticker",
            "created_at",
            "updated_at",
        )


class HoldingCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField(required=False)
    quantity = serializers.DecimalField(max_digits=50, decimal_places=30)
    average_purchase_price = serializers.DecimalField(
        max_digits=50,
        decimal_places=30,
        required=False,
        allow_null=True,
    )
    asset_type_slug = serializers.SlugField(required=False)
    custom_name = serializers.CharField(required=False, allow_blank=False)
    currency_code = serializers.CharField(required=False)


class AccountSerializer(serializers.ModelSerializer):
    active_schema_id = serializers.SerializerMethodField()
    holdings_count = serializers.IntegerField(source="holdings.count", read_only=True)

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
            "holdings_count",
            "position_mode",
            "allow_manual_overrides",
        )
        read_only_fields = (
            "id",
            "portfolio",
            "account_type",
            "classification",
            "last_synced",
            "created_at",
            "active_schema_id",
            "holdings_count",
        )

    def get_active_schema_id(self, obj):
        schema = obj.active_schema
        return schema.id if schema else None


class AccountCreateSerializer(serializers.Serializer):
    portfolio_id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    account_type_id = serializers.IntegerField()
    broker = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    classification_definition_id = serializers.IntegerField()
    position_mode = serializers.ChoiceField(choices=Account.PositionMode.choices, required=False)
    allow_manual_overrides = serializers.BooleanField(required=False)


class BrokerageConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokerageConnection
        fields = (
            "id",
            "account",
            "source_type",
            "provider",
            "external_account_id",
            "connection_label",
            "scopes",
            "consented_at",
            "consent_expires_at",
            "status",
            "last_synced_at",
            "last_error",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "scopes",
            "consented_at",
            "status",
            "last_synced_at",
            "last_error",
            "created_at",
            "updated_at",
        )


class BrokerageConnectionCreateSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    provider = serializers.ChoiceField(choices=BrokerageConnection.Provider.choices)
    source_type = serializers.ChoiceField(
        choices=BrokerageConnection.SourceType.choices,
        required=False,
    )
    external_account_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    connection_label = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # Exactly one of these should be supplied:
    # - public_token: from frontend provider Link flow
    # - token_ref: opaque reference from a connector service you control
    public_token = serializers.CharField(required=False, allow_blank=False)
    token_ref = serializers.CharField(required=False, allow_blank=False)

    consent_expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        public_token = attrs.get("public_token")
        token_ref = attrs.get("token_ref")

        if bool(public_token) == bool(token_ref):
            raise serializers.ValidationError(
                "Provide exactly one of public_token or token_ref."
            )


        return attrs


class BrokerageLinkSessionCreateSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    provider = serializers.ChoiceField(choices=BrokerageConnection.Provider.choices)
    source_type = serializers.ChoiceField(
        choices=BrokerageConnection.SourceType.choices,
        required=False,
    )
    redirect_uri = serializers.URLField(required=False)


class BrokerageSyncPayloadSerializer(serializers.Serializer):
    positions = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True,
    )
    prune_missing = serializers.BooleanField(default=False)


class TransactionSerializer(serializers.ModelSerializer):
    currency_code = serializers.CharField(source="currency.code", read_only=True)

    class Meta:
        model = AccountTransaction
        fields = (
            "id",
            "account",
            "holding",
            "asset",
            "event_type",
            "source",
            "external_transaction_id",
            "traded_at",
            "settled_at",
            "quantity",
            "unit_price",
            "gross_amount",
            "fees",
            "taxes",
            "net_amount",
            "currency",
            "currency_code",
            "note",
            "raw_payload",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "account",
            "source",
            "external_transaction_id",
            "raw_payload",
            "created_at",
            "updated_at",
        )


class TransactionCreateSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=AccountTransaction.EventType.choices)
    traded_at = serializers.DateTimeField()
    quantity = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    unit_price = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    gross_amount = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    fees = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    taxes = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    net_amount = serializers.DecimalField(max_digits=50, decimal_places=20, required=False, allow_null=True)
    currency_code = serializers.CharField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    asset_id = serializers.UUIDField(required=False)
    symbol = serializers.CharField(required=False)


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldingSnapshot
        fields = (
            "id",
            "holding",
            "as_of",
            "quantity",
            "average_purchase_price",
            "price",
            "value_profile_currency",
            "source",
            "created_at",
        )


class ReconciliationIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationIssue
        fields = (
            "id",
            "account",
            "connection",
            "holding",
            "issue_code",
            "severity",
            "status",
            "message",
            "metadata",
            "resolution_action",
            "resolution_note",
            "resolved_at",
            "created_at",
            "updated_at",
        )


class ReconciliationIssueUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ReconciliationIssue.Status.choices)
    resolution_action = serializers.ChoiceField(
        choices=ReconciliationIssue.ResolutionAction.choices,
        required=False,
    )
    resolution_note = serializers.CharField(required=False, allow_blank=True)


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountJob
        fields = (
            "id",
            "account",
            "connection",
            "job_type",
            "status",
            "idempotency_key",
            "payload",
            "result",
            "error",
            "run_after",
            "started_at",
            "finished_at",
            "attempts",
            "max_attempts",
            "created_at",
            "updated_at",
        )
