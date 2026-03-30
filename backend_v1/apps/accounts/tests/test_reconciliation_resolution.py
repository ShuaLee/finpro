from django.test import TestCase

from accounts.models import Account, AccountType, Holding, ReconciliationIssue
from accounts.services import ReconciliationService
from assets.models import AssetType
from assets.services import CustomAssetService
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class ReconciliationResolutionTest(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True},
        )
        AssetType.objects.get_or_create(name="Equity", created_by=None)

        user = User.objects.create_user(email="recon@example.com", password="StrongPass123!")
        ProfileBootstrapService.bootstrap(user=user)
        profile = user.profile
        portfolio = Portfolio.objects.get(profile=profile, kind=Portfolio.Kind.PERSONAL)

        account_type = AccountType.objects.create(
            name="Recon Brokerage",
            slug="recon-brokerage",
            is_system=True,
        )
        account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=portfolio,
            name="Recon Account",
            account_type=account_type,
        )
        asset = CustomAssetService.create(
            profile=profile,
            name="Recon Asset",
            asset_type_slug="equity",
            currency_code="USD",
        ).asset
        self.holding = Holding.objects.create(
            account=self.account,
            asset=asset,
            quantity="5",
            original_ticker="RCON",
        )

    def test_align_to_external_deletes_missing_external_holding(self):
        issue = ReconciliationIssue.objects.create(
            account=self.account,
            holding=self.holding,
            issue_code=ReconciliationIssue.IssueCode.MISSING_EXTERNAL_HOLDING,
            severity=ReconciliationIssue.Severity.WARNING,
            message="Missing externally",
            metadata={"symbol": "RCON"},
        )
        ReconciliationService.resolve_issue(
            issue=issue,
            action=ReconciliationIssue.ResolutionAction.ALIGN_TO_EXTERNAL,
        )
        self.assertFalse(Holding.objects.filter(id=self.holding.id).exists())
        issue.refresh_from_db()
        self.assertEqual(issue.status, ReconciliationIssue.Status.RESOLVED)

