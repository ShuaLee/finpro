from accounts.models import Holding
from schemas.services.schema_manager import SchemaManager


class HoldingService:
    @staticmethod
    def create(*, account, asset, quantity, average_purchase_price=None):
        holding = Holding.objects.create(
            account=account,
            asset=asset,
            quantity=quantity,
            average_purchase_price=average_purchase_price,
        )

        # Ensure SCVs after creation
        schema = account.active_schema
        if schema:
            SchemaManager.for_account(account).ensure_for_holding(holding)

        return holding

    @staticmethod
    def update(*, holding, quantity=None, average_purchase_price=None):
        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price

        holding.save()

        # Sync SCVs after update
        account = holding.account
        if account.active_schema:
            SchemaManager.for_account(account).sync_for_holding(holding)

        return holding
