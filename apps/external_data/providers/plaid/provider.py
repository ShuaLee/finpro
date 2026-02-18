from datetime import date

from external_data.exceptions import ExternalDataProviderUnavailable
from external_data.providers.plaid.constants import (
    PLAID_CLIENT_ID,
    PLAID_SECRET,
    plaid_base_url,
)
from external_data.providers.plaid.request import post_json


class PlaidProvider:
    name = "Plaid"

    def _auth_payload(self) -> dict:
        if not PLAID_CLIENT_ID or not PLAID_SECRET:
            raise ExternalDataProviderUnavailable("PLAID_CLIENT_ID/PLAID_SECRET are not configured.")
        return {
            "client_id": PLAID_CLIENT_ID,
            "secret": PLAID_SECRET,
        }

    def create_link_token(
        self,
        *,
        user_id: str,
        client_name: str = "Finpro",
        country_codes: list[str] | None = None,
        language: str = "en",
        webhook: str | None = None,
        redirect_uri: str | None = None,
    ) -> dict:
        payload = self._auth_payload()
        payload.update(
            {
                "user": {"client_user_id": user_id},
                "client_name": client_name,
                "products": ["investments"],
                "country_codes": country_codes or ["US", "CA"],
                "language": language,
            }
        )
        if webhook:
            payload["webhook"] = webhook
        if redirect_uri:
            payload["redirect_uri"] = redirect_uri
        return post_json(f"{plaid_base_url()}/link/token/create", payload)

    def exchange_public_token(self, *, public_token: str) -> dict:
        payload = self._auth_payload()
        payload["public_token"] = public_token
        return post_json(f"{plaid_base_url()}/item/public_token/exchange", payload)

    def get_item(self, *, access_token: str) -> dict:
        payload = self._auth_payload()
        payload["access_token"] = access_token
        return post_json(f"{plaid_base_url()}/item/get", payload)

    def get_investment_holdings(self, *, access_token: str) -> dict:
        payload = self._auth_payload()
        payload["access_token"] = access_token
        return post_json(f"{plaid_base_url()}/investments/holdings/get", payload)

    def get_investment_transactions(
        self,
        *,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        payload = self._auth_payload()
        payload.update(
            {
                "access_token": access_token,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "options": {"count": 100, "offset": 0},
            }
        )

        combined = {"accounts": [], "investment_transactions": [], "securities": []}
        total = None

        while True:
            data = post_json(f"{plaid_base_url()}/investments/transactions/get", payload)
            combined["accounts"] = data.get("accounts", combined["accounts"])
            combined["securities"] = data.get("securities", combined["securities"])
            combined["investment_transactions"].extend(data.get("investment_transactions", []))
            total = data.get("total_investment_transactions", total)

            fetched = len(combined["investment_transactions"])
            if total is None or fetched >= total:
                break
            payload["options"]["offset"] = fetched

        return combined

