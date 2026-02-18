from django.core.exceptions import ValidationError
from django.test import TestCase

from assets.models.commodity.precious_metal import PreciousMetalAsset
from assets.models.core import Asset, AssetType
from assets.models.crypto.crypto import CryptoAsset
from assets.models.custom.custom_asset import CustomAsset
from assets.models.real_estate.real_estate_type import RealEstateType
from fx.models.fx import FXCurrency
from profiles.models import Profile
from users.models import User


class AssetsProductionReadinessTests(TestCase):
    def setUp(self):
        self.usd = FXCurrency.objects.create(code="USD", name="US Dollar")

        self.user1 = User.objects.create_user(
            email="owner1@example.com",
            password="StrongPass123!",
        )
        self.user2 = User.objects.create_user(
            email="owner2@example.com",
            password="StrongPass123!",
        )

        self.profile1, _ = Profile.objects.get_or_create(
            user=self.user1,
            defaults={"currency": self.usd},
        )
        self.profile2, _ = Profile.objects.get_or_create(
            user=self.user2,
            defaults={"currency": self.usd},
        )

    def test_system_asset_type_slug_is_canonical(self):
        t = AssetType.objects.create(name="Cryptocurrency", created_by=None)
        self.assertEqual(t.slug, "crypto")

        re = AssetType.objects.create(name="Real Estate", created_by=None)
        self.assertEqual(re.slug, "real_estate")

    def test_custom_asset_cannot_use_another_users_asset_type(self):
        owner_only_type = AssetType.objects.create(
            name="Owner1 Special Type",
            created_by=self.profile1,
        )
        asset = Asset.objects.create(asset_type=owner_only_type)

        custom = CustomAsset(
            asset=asset,
            owner=self.profile2,
            name="Private Asset",
            currency=self.usd,
            reason=CustomAsset.Reason.USER,
        )

        with self.assertRaises(ValidationError):
            custom.full_clean()

    def test_custom_asset_name_is_unique_per_owner_and_type(self):
        t = AssetType.objects.create(name="Equity", created_by=None)

        a1 = Asset.objects.create(asset_type=t)
        CustomAsset.objects.create(
            asset=a1,
            owner=self.profile1,
            name="Acme Position",
            currency=self.usd,
            reason=CustomAsset.Reason.USER,
        )

        a2 = Asset.objects.create(asset_type=t)
        duplicate = CustomAsset(
            asset=a2,
            owner=self.profile1,
            name="acme position",
            currency=self.usd,
            reason=CustomAsset.Reason.USER,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_asset_extension_resolves_legacy_and_canonical_slugs(self):
        legacy_crypto_type = AssetType.objects.create(
            name="Legacy Crypto Type",
            slug="cryptocurrency",
            created_by=None,
        )
        canonical_crypto_type = AssetType.objects.create(
            name="Cryptocurrency",
            created_by=None,
        )

        legacy_asset = Asset.objects.create(asset_type=legacy_crypto_type)
        canonical_asset = Asset.objects.create(asset_type=canonical_crypto_type)

        CryptoAsset.objects.create(
            asset=legacy_asset,
            snapshot_id="00000000-0000-0000-0000-000000000001",
            base_symbol="BTC",
            pair_symbol="BTCUSD",
            name="Bitcoin",
            currency=self.usd,
        )
        CryptoAsset.objects.create(
            asset=canonical_asset,
            snapshot_id="00000000-0000-0000-0000-000000000002",
            base_symbol="ETH",
            pair_symbol="ETHUSD",
            name="Ethereum",
            currency=self.usd,
        )

        self.assertIsNotNone(legacy_asset.extension)
        self.assertIsNotNone(canonical_asset.extension)

    def test_precious_metal_requires_canonical_type(self):
        commodity_type = AssetType.objects.create(name="Commodity", created_by=None)
        precious_type = AssetType.objects.create(name="Precious Metal", created_by=None)

        commodity_asset = Asset.objects.create(asset_type=commodity_type)
        precious_asset = Asset.objects.create(asset_type=precious_type)

        from assets.models.commodity.commodity import CommodityAsset

        commodity = CommodityAsset.objects.create(
            asset=commodity_asset,
            snapshot_id="00000000-0000-0000-0000-000000000003",
            symbol="GCUSD",
            currency=self.usd,
        )

        pm = PreciousMetalAsset(
            asset=precious_asset,
            metal=PreciousMetalAsset.Metal.GOLD,
            commodity=commodity,
        )
        pm.full_clean()

    def test_asset_type_name_uniqueness_enforced_in_model_validation(self):
        AssetType.objects.create(name="Equity", created_by=None)
        duplicate = AssetType(name="equity", created_by=None)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_real_estate_type_name_uniqueness_enforced_in_model_validation(self):
        RealEstateType.objects.create(name="Condo", created_by=self.profile1)
        duplicate = RealEstateType(name="condo", created_by=self.profile1)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()
