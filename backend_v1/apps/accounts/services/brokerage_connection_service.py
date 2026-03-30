from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import BrokerageConnection

from .brokerage_adapters import get_adapter
from .secret_vault import BrokerageSecretVault


class BrokerageConnectionService:
    PROVIDER_TO_SOURCE_TYPE = {
        BrokerageConnection.Provider.MANUAL: BrokerageConnection.SourceType.BROKERAGE,
        BrokerageConnection.Provider.PLAID: BrokerageConnection.SourceType.BROKERAGE,
        BrokerageConnection.Provider.ALPACA: BrokerageConnection.SourceType.BROKERAGE,
        BrokerageConnection.Provider.COINBASE: BrokerageConnection.SourceType.CRYPTO_EXCHANGE,
        BrokerageConnection.Provider.KRAKEN: BrokerageConnection.SourceType.CRYPTO_EXCHANGE,
        BrokerageConnection.Provider.WALLET_CONNECT: BrokerageConnection.SourceType.WALLET,
    }

    @staticmethod
    def resolve_source_type(*, provider: str, source_type: str | None) -> str:
        if source_type:
            return source_type
        return BrokerageConnectionService.PROVIDER_TO_SOURCE_TYPE.get(
            provider,
            BrokerageConnection.SourceType.BROKERAGE,
        )

    @staticmethod
    @transaction.atomic
    def connect_read_only(
        *,
        account,
        provider: str,
        source_type: str | None,
        public_token: str | None,
        token_ref: str | None,
        external_account_id: str | None,
        connection_label: str | None,
        consent_expires_at,
    ):
        if bool(public_token) == bool(token_ref):
            raise ValidationError("Provide exactly one of public_token or token_ref.")

        resolved_source_type = BrokerageConnectionService.resolve_source_type(
            provider=provider,
            source_type=source_type,
        )

        scopes = ["holdings.read"]
        resolved_external_account_id = external_account_id

        if public_token:
            adapter = get_adapter(provider)
            exchange = adapter.exchange_public_token(public_token=public_token)
            resolved_token_ref = exchange.token_ref
            if exchange.external_account_id:
                resolved_external_account_id = exchange.external_account_id
            if exchange.scopes:
                scopes = exchange.scopes
        else:
            resolved_token_ref = token_ref

        if not resolved_token_ref:
            raise ValidationError("A token reference could not be resolved.")

        if provider == BrokerageConnection.Provider.PLAID and resolved_token_ref.startswith("plaid:"):
            raw_access_token = resolved_token_ref.split(":", 1)[1]
            resolved_token_ref = BrokerageSecretVault.store(
                provider=provider,
                plaintext=raw_access_token,
            )

        connection, _ = BrokerageConnection.objects.update_or_create(
            account=account,
            defaults={
                "provider": provider,
                "source_type": resolved_source_type,
                "external_account_id": resolved_external_account_id,
                "connection_label": connection_label,
                "access_token_ref": resolved_token_ref,
                "scopes": scopes,
                "consented_at": timezone.now(),
                "consent_expires_at": consent_expires_at,
                "status": BrokerageConnection.Status.ACTIVE,
                "last_error": None,
            },
        )
        return connection

    @staticmethod
    def create_link_session(
        *,
        provider: str,
        redirect_uri: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        adapter = get_adapter(provider)
        return adapter.create_link_session(
            connection=None,
            redirect_uri=redirect_uri,
            user_id=user_id,
        )

    @staticmethod
    @transaction.atomic
    def disconnect(*, connection: BrokerageConnection):
        if connection.access_token_ref and connection.access_token_ref.startswith("vault:"):
            BrokerageSecretVault.revoke(reference=connection.access_token_ref)
        connection.status = BrokerageConnection.Status.DISCONNECTED
        connection.last_error = None
        connection.access_token_ref = None
        connection.scopes = []
        connection.save(
            update_fields=[
                "status",
                "last_error",
                "access_token_ref",
                "scopes",
                "updated_at",
            ]
        )
        return connection
