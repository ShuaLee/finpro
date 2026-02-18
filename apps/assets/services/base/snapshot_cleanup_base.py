import logging

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from assets.models.core import Asset
from assets.models.custom.custom_asset import CustomAsset

logger = logging.getLogger(__name__)


class SnapshotCleanupBaseService:
    """
    Base service for cleaning stale market assets.

    If accounts/schemas apps are disabled, cleanup becomes a safe no-op.
    """

    extension_model = None
    snapshot_model = None
    name_attr = None
    currency_attr = None

    @classmethod
    @transaction.atomic
    def run(cls):
        cls._validate_configuration()

        snapshot = cls.snapshot_model.objects.first()
        if not snapshot:
            return

        holding_model = cls._get_holding_model()
        if holding_model is None:
            logger.warning(
                "%s skipped: accounts app unavailable; cannot evaluate holdings.",
                cls.__name__,
            )
            return

        stale_extensions = (
            cls.extension_model.objects.exclude(snapshot_id=snapshot.current_snapshot)
            .select_related("asset")
            .order_by("pk")
        )

        for extension in stale_extensions:
            cls._handle_stale_extension(extension, holding_model)

    @classmethod
    def _validate_configuration(cls):
        missing = [
            name
            for name in ("extension_model", "snapshot_model", "name_attr", "currency_attr")
            if getattr(cls, name) is None
        ]
        if missing:
            raise ImproperlyConfigured(
                f"{cls.__name__} missing configuration: {', '.join(missing)}"
            )

    @staticmethod
    def _get_holding_model():
        try:
            return apps.get_model("accounts", "Holding")
        except (LookupError, ValueError):
            return None

    @staticmethod
    def _notify_holdings_changed(holdings_qs):
        try:
            from schemas.services.orchestration import SchemaOrchestrationService
        except Exception:
            return
        SchemaOrchestrationService.holdings_changed(holdings_qs)

    @classmethod
    def _handle_stale_extension(cls, extension, holding_model):
        asset = extension.asset
        holdings = holding_model.objects.select_for_update().filter(asset=asset)

        if not holdings.exists():
            extension.delete()
            asset.delete()
            return

        cls._convert_asset_per_profile(extension, holding_model)
        extension.delete()

        if not holding_model.objects.filter(asset=asset).exists():
            asset.delete()

    @classmethod
    def _convert_asset_per_profile(cls, extension, holding_model):
        asset = extension.asset

        profile_ids = (
            holding_model.objects.select_for_update()
            .filter(asset=asset)
            .values_list("account__portfolio__profile_id", flat=True)
            .distinct()
        )

        for profile_id in profile_ids:
            cls._clone_asset_for_profile(
                extension=extension,
                profile_id=profile_id,
                holding_model=holding_model,
            )

    @classmethod
    def _clone_asset_for_profile(cls, *, extension, profile_id, holding_model):
        asset = extension.asset

        name = getattr(extension, cls.name_attr, None)
        currency = getattr(extension, cls.currency_attr, None)

        if not name:
            raise RuntimeError(f"{cls.__name__}: Missing name for asset {asset.id}")
        if not currency:
            raise RuntimeError(f"{cls.__name__}: Missing currency for asset {asset.id}")

        custom_asset = (
            CustomAsset.objects.select_related("asset")
            .filter(owner_id=profile_id, name=name, reason=CustomAsset.Reason.MARKET)
            .first()
        )

        if custom_asset:
            new_asset = custom_asset.asset
        else:
            new_asset = Asset.objects.create(asset_type=asset.asset_type)
            CustomAsset.objects.create(
                asset=new_asset,
                owner_id=profile_id,
                name=name,
                currency=currency,
                reason=CustomAsset.Reason.MARKET,
                requires_review=True,
            )

        holding_model.objects.filter(
            asset=asset,
            account__portfolio__profile_id=profile_id,
        ).update(asset=new_asset)

        migrated_holdings = holding_model.objects.filter(
            asset=new_asset,
            account__portfolio__profile_id=profile_id,
        ).select_related("account")

        if migrated_holdings.exists():
            cls._notify_holdings_changed(migrated_holdings)
