from django.test import TestCase

from accounts.models import Account, AccountJob, AccountType
from accounts.services import AccountJobService
from assets.models import AssetType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from portfolios.models import Portfolio
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class AccountJobServiceTest(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(
            slug="free",
            defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True},
        )
        AssetType.objects.get_or_create(name="Equity", created_by=None)

        user = User.objects.create_user(email="jobs@example.com", password="StrongPass123!")
        ProfileBootstrapService.bootstrap(user=user)
        profile = user.profile
        portfolio = Portfolio.objects.get(profile=profile, kind=Portfolio.Kind.PERSONAL)

        account_type = AccountType.objects.create(
            name="Jobs Brokerage",
            slug="jobs-brokerage",
            is_system=True,
        )
        account_type.allowed_asset_types.add(AssetType.objects.get(slug="equity"))

        self.account = Account.objects.create(
            portfolio=portfolio,
            name="Jobs Account",
            account_type=account_type,
        )

    def test_enqueue_is_idempotent_when_key_matches(self):
        j1 = AccountJobService.enqueue(
            account=self.account,
            job_type=AccountJob.JobType.SNAPSHOT,
            idempotency_key="snap:1",
        )
        j2 = AccountJobService.enqueue(
            account=self.account,
            job_type=AccountJob.JobType.SNAPSHOT,
            idempotency_key="snap:1",
        )
        self.assertEqual(j1.id, j2.id)

