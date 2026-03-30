from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import Asset, AssetType, RealEstateType
from fx.models.country import Country
from fx.models.fx import FXCurrency
from profiles.services.bootstrap_service import ProfileBootstrapService
from subscriptions.models import Plan
from users.models import User


class AssetsAPITests(APITestCase):
    def setUp(self):
        FXCurrency.objects.get_or_create(
            code="USD",
            defaults={"name": "US Dollar", "is_active": True},
        )
        FXCurrency.objects.get_or_create(
            code="CAD",
            defaults={"name": "Canadian Dollar", "is_active": True},
        )
        Country.objects.get_or_create(
            code="US",
            defaults={"name": "United States", "is_active": True},
        )
        Country.objects.get_or_create(
            code="CA",
            defaults={"name": "Canada", "is_active": True},
        )
        Plan.objects.get_or_create(
            slug="free",
            defaults={
                "name": "Free",
                "tier": Plan.Tier.FREE,
                "is_active": True,
            },
        )

        AssetType.objects.get_or_create(name="Equity", created_by=None)
        AssetType.objects.get_or_create(name="Real Estate", created_by=None)

        self.user1 = User.objects.create_user(
            email="assets-owner-1@example.com",
            password="StrongPass123!",
        )
        self.user2 = User.objects.create_user(
            email="assets-owner-2@example.com",
            password="StrongPass123!",
        )
        ProfileBootstrapService.bootstrap(user=self.user1)
        ProfileBootstrapService.bootstrap(user=self.user2)

        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile

        self.system_real_estate_type = RealEstateType.objects.create(
            name="Apartment",
            created_by=None,
        )
        self.user2_real_estate_type = RealEstateType.objects.create(
            name="User2 Private Type",
            created_by=self.profile2,
        )

    def test_custom_asset_is_owner_scoped(self):
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post(
            reverse("custom-asset-list-create"),
            {
                "name": "Private Position",
                "asset_type_slug": "equity",
                "currency_code": "USD",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        asset_id = create_response.json()["id"]

        self.client.force_authenticate(user=self.user2)
        other_response = self.client.get(
            reverse("custom-asset-detail", kwargs={"asset_id": asset_id})
        )
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_real_estate_asset_is_owner_scoped(self):
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post(
            reverse("real-estate-asset-list-create"),
            {
                "property_type_id": self.system_real_estate_type.id,
                "country_code": "US",
                "currency_code": "USD",
                "city": "Austin",
                "address": "123 Main St",
                "is_owner_occupied": True,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        asset_id = create_response.json()["id"]

        self.client.force_authenticate(user=self.user2)
        other_response = self.client.get(
            reverse("real-estate-asset-detail", kwargs={"asset_id": asset_id})
        )
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_real_estate_create_rejects_other_users_custom_type(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(
            reverse("real-estate-asset-list-create"),
            {
                "property_type_id": self.user2_real_estate_type.id,
                "country_code": "US",
                "currency_code": "USD",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_asset_type_crud(self):
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post(
            reverse("asset-type-custom-create"),
            {"name": "My Venture Assets"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        type_id = create_response.json()["id"]

        patch_response = self.client.patch(
            reverse("asset-type-custom-detail", kwargs={"type_id": type_id}),
            {"name": "My Venture Holdings"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.json()["name"], "My Venture Holdings")

        delete_response = self.client.delete(
            reverse("asset-type-custom-detail", kwargs={"type_id": type_id})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_custom_asset_delete_removes_base_asset_row(self):
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post(
            reverse("custom-asset-list-create"),
            {
                "name": "Delete Me",
                "asset_type_slug": "equity",
                "currency_code": "USD",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        asset_id = create_response.json()["id"]

        delete_response = self.client.delete(
            reverse("custom-asset-detail", kwargs={"asset_id": asset_id})
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Asset.objects.filter(id=asset_id).exists())
