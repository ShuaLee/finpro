from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.assets.models import Asset, AssetPrice, AssetType
from apps.holdings.models import Container, Holding, Portfolio


class HoldingFactAndOverrideAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="holding-facts@example.com",
            password="StrongPass123!",
        )
        self.client.force_authenticate(self.user)
        self.portfolio = Portfolio.objects.create(profile=self.user.profile, name="Main")
        self.container = Container.objects.create(portfolio=self.portfolio, name="Brokerage")
        self.asset_type = AssetType.objects.create(name="Equity")
        self.asset = Asset.objects.create(
            asset_type=self.asset_type,
            name="Apple Inc.",
            symbol="AAPL",
            data={"sector": "Technology", "industry": "Consumer Electronics"},
        )
        AssetPrice.objects.create(asset=self.asset, price=Decimal("200"))
        self.holding = Holding.objects.create(
            container=self.container,
            asset=self.asset,
            quantity=Decimal("2"),
            unit_value=Decimal("190"),
        )

    def test_create_fact_definition_upsert_value_and_override(self):
        definition_response = self.client.post(
            reverse("holding-fact-definition-list-create"),
            {
                "portfolio": self.portfolio.pk,
                "key": "custom_sector",
                "label": "Custom Sector",
                "data_type": "string",
            },
            format="json",
        )
        self.assertEqual(definition_response.status_code, 201)
        definition_id = definition_response.json()["id"]

        value_response = self.client.post(
            reverse("holding-fact-list-upsert", kwargs={"pk": self.holding.pk}),
            {
                "definition": definition_id,
                "value": "Gold Equities",
            },
            format="json",
        )
        self.assertEqual(value_response.status_code, 201)

        override_response = self.client.post(
            reverse("holding-override-list-upsert", kwargs={"pk": self.holding.pk}),
            {
                "key": "sector",
                "data_type": "string",
                "value": "AI Infrastructure",
            },
            format="json",
        )
        self.assertEqual(override_response.status_code, 201)

        detail_response = self.client.get(
            reverse("holding-detail", kwargs={"pk": self.holding.pk}),
        )
        self.assertEqual(detail_response.status_code, 200)
        body = detail_response.json()
        self.assertEqual(body["effective_price"], "190.000000000000000000")
        self.assertEqual(body["effective_sector"], "AI Infrastructure")
        self.assertEqual(len(body["fact_values"]), 1)
        self.assertEqual(body["fact_values"][0]["definition_key"], "custom_sector")
        self.assertEqual(body["fact_values"][0]["typed_value"], "Gold Equities")
        self.assertEqual(len(body["overrides"]), 1)
