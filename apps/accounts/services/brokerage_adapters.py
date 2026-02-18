from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from external_data.providers.plaid import PLAID_PROVIDER

from .secret_vault import BrokerageSecretVault

@dataclass
class BrokeragePosition:
    symbol: str
    quantity: Decimal
    average_cost: Decimal | None = None


@dataclass
class TokenExchangeResult:
    token_ref: str
    external_account_id: str | None = None
    scopes: list[str] | None = None


class BrokerageAdapter:
    def create_link_session(
        self,
        *,
        connection,
        redirect_uri: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        raise NotImplementedError

    def exchange_public_token(self, *, public_token: str) -> TokenExchangeResult:
        raise NotImplementedError

    def fetch_positions(self, connection) -> list[BrokeragePosition]:
        raise NotImplementedError

    def fetch_transactions(self, connection, *, days: int = 30) -> list[dict]:
        return []


class ManualBrokerageAdapter(BrokerageAdapter):
    """
    Development/testing adapter.

    - create_link_session returns a synthetic link payload.
    - exchange_public_token returns an opaque token reference.
    - fetch_positions returns [] by default; use sync-payload endpoint for manual imports.
    """

    def create_link_session(
        self,
        *,
        connection,
        redirect_uri: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        return {
            "provider": "manual",
            "link_token": "manual-link-token",
            "redirect_uri": redirect_uri,
            "note": "Manual provider does not require hosted auth.",
        }

    def exchange_public_token(self, *, public_token: str) -> TokenExchangeResult:
        return TokenExchangeResult(
            token_ref=f"manual:{public_token}",
            external_account_id=None,
            scopes=["holdings.read"],
        )

    def fetch_positions(self, connection) -> list[BrokeragePosition]:
        return []

    def fetch_transactions(self, connection, *, days: int = 30) -> list[dict]:
        transactions = (connection.credentials or {}).get("transactions", [])
        rows = []
        for tx in transactions:
            rows.append(
                {
                    "external_transaction_id": tx.get("external_transaction_id"),
                    "event_type": tx.get("event_type", "adjustment"),
                    "symbol": tx.get("symbol"),
                    "traded_at": tx.get("traded_at"),
                    "quantity": tx.get("quantity"),
                    "unit_price": tx.get("unit_price"),
                    "gross_amount": tx.get("gross_amount"),
                    "fees": tx.get("fees"),
                    "taxes": tx.get("taxes"),
                    "net_amount": tx.get("net_amount"),
                    "note": tx.get("note"),
                    "raw_payload": tx,
                }
            )
        return rows


class PlaidBrokerageAdapter(BrokerageAdapter):
    EVENT_TYPE_MAP = {
        "buy": "buy",
        "sell": "sell",
        "cash": "deposit",
        "transfer": "transfer_in",
        "dividend": "dividend",
        "interest": "interest",
        "fee": "fee",
        "tax": "tax",
    }

    def create_link_session(
        self,
        *,
        connection,
        redirect_uri: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        effective_user_id = user_id or "anonymous"
        if connection is not None and not user_id:
            effective_user_id = str(connection.account.portfolio.profile.user_id)
        data = PLAID_PROVIDER.create_link_token(
            user_id=effective_user_id,
            redirect_uri=redirect_uri,
        )
        return {
            "provider": "plaid",
            "link_token": data.get("link_token"),
            "expiration": data.get("expiration"),
            "request_id": data.get("request_id"),
        }

    def exchange_public_token(self, *, public_token: str) -> TokenExchangeResult:
        data = PLAID_PROVIDER.exchange_public_token(public_token=public_token)
        access_token = data.get("access_token")
        item_id = data.get("item_id")
        return TokenExchangeResult(
            token_ref=f"plaid:{access_token}",
            external_account_id=item_id,
            scopes=["holdings.read", "transactions.read"],
        )

    def _extract_access_token(self, connection) -> str:
        token_ref = connection.access_token_ref or ""
        if token_ref.startswith("vault:"):
            return BrokerageSecretVault.retrieve(reference=token_ref)
        if token_ref.startswith("plaid:"):
            # Legacy compatibility path.
            return token_ref.split(":", 1)[1]
        raise ValueError("Invalid Plaid token reference.")

    def fetch_positions(self, connection) -> list[BrokeragePosition]:
        access_token = self._extract_access_token(connection)
        data = PLAID_PROVIDER.get_investment_holdings(access_token=access_token)
        securities = {s.get("security_id"): s for s in data.get("securities", [])}

        positions: list[BrokeragePosition] = []
        for holding in data.get("holdings", []):
            sec = securities.get(holding.get("security_id")) or {}
            symbol = (sec.get("ticker_symbol") or "").strip().upper()
            quantity = holding.get("quantity")
            if not symbol or quantity is None:
                continue
            positions.append(
                BrokeragePosition(
                    symbol=symbol,
                    quantity=Decimal(str(quantity)),
                    average_cost=Decimal(str(holding.get("cost_basis"))) if holding.get("cost_basis") is not None else None,
                )
            )
        return positions

    def fetch_transactions(self, connection, *, days: int = 30) -> list[dict]:
        access_token = self._extract_access_token(connection)
        end = date.today()
        start = end - timedelta(days=days)
        data = PLAID_PROVIDER.get_investment_transactions(
            access_token=access_token,
            start_date=start,
            end_date=end,
        )
        securities = {s.get("security_id"): s for s in data.get("securities", [])}

        out = []
        for row in data.get("investment_transactions", []):
            sec = securities.get(row.get("security_id")) or {}
            tx_type = (row.get("type") or "").strip().lower()
            subtype = (row.get("subtype") or "").strip().lower()
            event_type = self.EVENT_TYPE_MAP.get(subtype) or self.EVENT_TYPE_MAP.get(tx_type) or "adjustment"
            symbol = (sec.get("ticker_symbol") or "").strip().upper() or None
            out.append(
                {
                    "external_transaction_id": row.get("investment_transaction_id"),
                    "event_type": event_type,
                    "symbol": symbol,
                    "traded_at": row.get("date"),
                    "quantity": row.get("quantity"),
                    "unit_price": row.get("price"),
                    "gross_amount": row.get("amount"),
                    "fees": None,
                    "taxes": None,
                    "net_amount": row.get("amount"),
                    "note": row.get("name"),
                    "raw_payload": row,
                }
            )
        return out


class PlaceholderProviderAdapter(BrokerageAdapter):
    """
    Placeholder for real providers (Plaid/Alpaca/Coinbase/etc).
    Implement this in your connector integration layer.
    """

    def __init__(self, provider: str):
        self.provider = provider

    def create_link_session(
        self,
        *,
        connection,
        redirect_uri: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        return {
            "provider": self.provider,
            "link_token": None,
            "redirect_uri": redirect_uri,
            "note": "Implement provider-specific link session generation.",
        }

    def exchange_public_token(self, *, public_token: str) -> TokenExchangeResult:
        # This should call your provider SDK/backend and return an opaque token reference.
        return TokenExchangeResult(
            token_ref=f"{self.provider}:public:{public_token}",
            external_account_id=None,
            scopes=["holdings.read"],
        )

    def fetch_positions(self, connection) -> list[BrokeragePosition]:
        # Pull sync should be implemented provider-by-provider.
        return []


def get_adapter(provider: str) -> BrokerageAdapter:
    provider = (provider or "").strip().lower()
    if provider == "manual":
        return ManualBrokerageAdapter()
    if provider == "plaid":
        return PlaidBrokerageAdapter()
    if provider in {"alpaca", "coinbase", "kraken", "wallet_connect"}:
        return PlaceholderProviderAdapter(provider=provider)
    raise ValueError(f"Unsupported brokerage provider: {provider}")
