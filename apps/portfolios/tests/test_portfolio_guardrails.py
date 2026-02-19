from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from fx.models import Country, FXCurrency
from portfolios.models import Portfolio
from profiles.services import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class PortfolioGuardrailTests(TestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(code="USD", defaults={"name": "US Dollar", "is_active": True})
        Country.objects.get_or_create(code="US", defaults={"name": "United States", "is_active": True})
        Plan.objects.get_or_create(slug="free", defaults={"name": "Free", "tier": Plan.Tier.FREE, "is_active": True})

        self.user = User.objects.create_user(
            email="portfolio-guardrail@example.com",
            password="StrongPass123!",
            email_verified_at=timezone.now(),
        )
        ProfileBootstrapService.bootstrap(user=self.user)
        self.personal = Portfolio.objects.get(profile=self.user.profile, kind=Portfolio.Kind.PERSONAL)

    def test_personal_portfolio_kind_is_immutable(self):
        self.personal.kind = Portfolio.Kind.CLIENT
        self.personal.client_name = "Client A"
        with self.assertRaises(ValidationError):
            self.personal.save()

    def test_personal_portfolio_name_is_immutable(self):
        self.personal.name = "Renamed Main"
        with self.assertRaises(ValidationError):
            self.personal.save()
