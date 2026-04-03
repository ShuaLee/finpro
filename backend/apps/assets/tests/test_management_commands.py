from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.assets.management.commands.seed_asset_types import SYSTEM_ASSET_TYPES
from apps.assets.models import AssetType


class SeedAssetTypesCommandTests(TestCase):
    def test_seed_asset_types_creates_and_is_idempotent(self):
        out = StringIO()

        call_command("seed_asset_types", stdout=out)

        seeded_names = set(
            AssetType.objects.filter(created_by__isnull=True).values_list("name", flat=True)
        )
        expected_names = {item["name"] for item in SYSTEM_ASSET_TYPES}

        self.assertTrue(expected_names.issubset(seeded_names))

        first_count = AssetType.objects.filter(created_by__isnull=True).count()

        out = StringIO()
        call_command("seed_asset_types", stdout=out)
        second_count = AssetType.objects.filter(created_by__isnull=True).count()

        self.assertEqual(first_count, second_count)
