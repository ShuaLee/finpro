from django.db import transaction

from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset
from accounts.models import Holding


class SnapshotCleanupBaseService:
    """
    Base service for cleaning up stale market assets.

    Rules:
    - If an asset has NO holdings → delete Asset
    - If an asset HAS holdings → convert to CustomAsset
      - One CustomAsset PER profile
      - Re-point holdings
      - Remove market extension
    """

    extension_model = None        # e.g. EquityAsset
    snapshot_model = None         # e.g. EquitySnapshotID
    name_attr = None              # e.g. "ticker"
    currency_attr = None          # e.g. "currency"

    @classmethod
    @transaction.atomic
    def run(cls):
        snapshot = cls.snapshot_model.objects.first()
        if not snapshot:
            return

        stale_extensions = cls.extension_model.objects.exclude(
            snapshot_id=snapshot.current_snapshot
        ).select_related("asset")

        for extension in stale_extensions:
            cls._handle_stale_extension(extension)

    # --------------------------------------------------
    # Core logic
    # --------------------------------------------------
    @classmethod
    def _handle_stale_extension(cls, extension):
        asset = extension.asset

        if not asset.holdings.exists():
            # No holdings → safe delete
            asset.delete()
            return

        # Holdings exist → split per profile
        cls._convert_asset_per_profile(extension)

        # Remove market extension AFTER split
        extension.delete()

        # Delete original asset if unused
        if not asset.holdings.exists():
            asset.delete()

    @classmethod
    def _convert_asset_per_profile(cls, extension):
        asset = extension.asset

        # Group holdings by profile
        profile_ids = (
            Holding.objects
            .filter(asset=asset)
            .values_list("account__portfolio__profile_id", flat=True)
            .distinct()
        )

        for profile_id in profile_ids:
            cls._clone_asset_for_profile(
                extension=extension,
                profile_id=profile_id,
            )

    @classmethod
    def _clone_asset_for_profile(cls, *, extension, profile_id):
        asset = extension.asset

        # 1️⃣ Create new Asset
        new_asset = Asset.objects.create(
            asset_type=asset.asset_type
        )

        # 2️⃣ Create CustomAsset
        CustomAsset.objects.create(
            asset=new_asset,
            owner_id=profile_id,
            name=getattr(extension, cls.name_attr),
            currency=getattr(extension, cls.currency_attr),
            reason=CustomAsset.Reason.MARKET,
        )

        # 3️⃣ Re-point holdings
        Holding.objects.filter(
            asset=asset,
            account__portfolio__profile_id=profile_id,
        ).update(asset=new_asset)
