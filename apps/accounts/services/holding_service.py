from accounts.models import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


class HoldingService:
    @staticmethod
    def create(*, account, asset, quantity, average_purchase_price=None):
        holding = Holding.objects.create(
            account=account,
            asset=asset,
            quantity=quantity,
            average_purchase_price=average_purchase_price,
            source=Holding.SOURCE_ASSET,
            original_ticker=getattr(asset.equity, "ticker", None),
            custom_reason=None,
        )

        SCVRefreshService.holding_changed(holding)
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
            SCVRefreshService.holding_changed(holding)

        return holding
