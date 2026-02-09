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

        has_holdings = Holding.objects.filter(asset=asset).exists()

        if not has_holdings:
            asset.delete()
            return

        # Holdings exist → split per profile
        cls._convert_asset_per_profile(extension)

        # Remove market extension AFTER split
        extension.delete()

        # Delete original asset if no longer referenced
        if not Holding.objects.filter(asset=asset).exists():
            asset.delete()

    @classmethod
    def _convert_asset_per_profile(cls, extension):
        asset = extension.asset

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

        try:
            name = getattr(extension, cls.name_attr)
            currency = getattr(extension, cls.currency_attr)
        except AttributeError as e:
            raise ImproperlyConfigured(
                f"{cls.__name__}: extension missing required attribute ({e})"
            )

        # 1️⃣ Create or reuse CustomAsset
        custom_asset, created = CustomAsset.objects.get_or_create(
            owner_id=profile_id,
            name=name,
            defaults={
                "asset": Asset.objects.create(
                    asset_type=asset.asset_type
                ),
                "currency": currency,
                "reason": CustomAsset.Reason.MARKET,
            },
        )

        # 2️⃣ Re-point holdings
        holdings = Holding.objects.filter(
            asset=asset,
            account__portfolio__profile_id=profile_id,
        )

        holdings.update(asset=custom_asset.asset)

        # 3️⃣ Recompute schema values
        for holding in holdings:
            SCVRefreshService.holding_changed(holding)
