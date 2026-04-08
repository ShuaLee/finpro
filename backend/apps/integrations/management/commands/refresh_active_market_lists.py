from django.core.management.base import BaseCommand

from apps.integrations.services import (
    ActiveCommoditySyncService,
    ActiveCryptoSyncService,
    ActiveEquitySyncService,
    HeldEquityReviewService,
    HeldMarketAssetReviewService,
)


class Command(BaseCommand):
    help = "Refresh the current active FMP market lists and review tracked public assets."

    def handle(self, *args, **options):
        equity_result = ActiveEquitySyncService.refresh_from_fmp()
        crypto_result = ActiveCryptoSyncService.refresh_from_fmp()
        commodity_result = ActiveCommoditySyncService.refresh_from_fmp()
        equity_review_result = HeldEquityReviewService.review_all_tracked_equities()
        market_review_result = HeldMarketAssetReviewService.review_all_tracked_assets()
        self.stdout.write(
            self.style.SUCCESS(
                str(
                    {
                        "equities": equity_result,
                        "cryptos": crypto_result,
                        "commodities": commodity_result,
                        "equity_review": equity_review_result,
                        "market_review": market_review_result,
                    }
                )
            )
        )
