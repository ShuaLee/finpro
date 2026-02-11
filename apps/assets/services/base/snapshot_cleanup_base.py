from django.db import transaction
from django.core.exceptions import ImproperlyConfigured

from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset
from accounts.models import Holding
from schemas.services.scv_refresh_service import SCVRefreshService


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

    # --------------------------------------------------
    # Entry
    # --------------------------------------------------
    @classmethod
    @transaction.atomic
    def run(cls):
        cls._validate_configuration()

        snapshot = cls.snapshot_model.objects.first()
        if not snapshot:
            return

        stale_extensions = (
            cls.extension_model.objects
            .exclude(snapshot_id=snapshot.current_snapshot)
            .select_related("asset")
            .order_by("pk")  # deterministic + safer
        )

        for extension in stale_extensions:
            cls._handle_stale_extension(extension)

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------
    @classmethod
    def _validate_configuration(cls):
        missing = [
            name for name in (
                "extension_model",
                "snapshot_model",
                "name_attr",
                "currency_attr",
            )
            if getattr(cls, name) is None
        ]

        if missing:
            raise ImproperlyConfigured(
                f"{cls.__name__} missing configuration: {', '.join(missing)}"
            )

    # --------------------------------------------------
    # Core logic
    # --------------------------------------------------
    @classmethod
    def _handle_stale_extension(cls, extension):
        asset = extension.asset

        holdings = (
            Holding.objects
            .select_for_update()
            .filter(asset=asset)
        )

        if not holdings.exists():
            # Truly unused → safe delete
            extension.delete()
            asset.delete()
            return

        # Holdings exist → MUST convert
        cls._convert_asset_per_profile(extension)

        # Remove market extension
        extension.delete()

        # If no holdings remain on original asset → delete it
        if not Holding.objects.filter(asset=asset).exists():
            asset.delete()

    @classmethod
    def _convert_asset_per_profile(cls, extension):
        asset = extension.asset

        profile_ids = (
            Holding.objects
            .select_for_update()
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

        name = getattr(extension, cls.name_attr, None)
        currency = getattr(extension, cls.currency_attr, None)

        if not name:
            raise RuntimeError(
                f"{cls.__name__}: Missing name for asset {asset.id}"
            )

        if not currency:
            raise RuntimeError(
                f"{cls.__name__}: Missing currency for asset {asset.id}"
            )

        # Reuse existing MARKET custom asset if present
        custom_asset = (
            CustomAsset.objects
            .select_related("asset")
            .filter(
                owner_id=profile_id,
                name=name,
                reason=CustomAsset.Reason.MARKET,
            )
            .first()
        )

        if custom_asset:
            new_asset = custom_asset.asset
        else:
            new_asset = Asset.objects.create(
                asset_type=asset.asset_type
            )

            CustomAsset.objects.create(
                asset=new_asset,
                owner_id=profile_id,
                name=name,
                currency=currency,
                reason=CustomAsset.Reason.MARKET,
                requires_review=True,
            )

        # Re-point holdings
        Holding.objects.filter(
            asset=asset,
            account__portfolio__profile_id=profile_id,
        ).update(asset=new_asset)

        # Trigger SCV refresh AFTER migration
        for holding in Holding.objects.filter(
            asset=new_asset,
            account__portfolio__profile_id=profile_id,
        ):
            SCVRefreshService.holding_changed(holding)
