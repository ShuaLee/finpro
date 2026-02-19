import logging
from decimal import Decimal

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
            cls._handle_stale_extension(
                extension=extension,
                holding_model=holding_model,
                active_snapshot_id=snapshot.current_snapshot,
            )

        cls._relink_market_custom_assets(
            holding_model=holding_model,
            active_snapshot_id=snapshot.current_snapshot,
        )

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
    def _handle_stale_extension(cls, *, extension, holding_model, active_snapshot_id):
        asset = extension.asset
        holdings = holding_model.objects.select_for_update().filter(asset=asset)

        if not holdings.exists():
            extension.delete()
            asset.delete()
            return

        replacement_asset = cls._find_active_replacement_asset(
            extension=extension,
            active_snapshot_id=active_snapshot_id,
        )
        if replacement_asset:
            cls._relink_holdings_to_market_asset(
                holdings_qs=holdings,
                target_asset=replacement_asset,
                holding_model=holding_model,
            )

        remaining_holdings = holding_model.objects.select_for_update().filter(asset=asset)
        if not remaining_holdings.exists():
            extension.delete()
            asset.delete()
            return

        cls._convert_asset_per_profile(extension, holding_model)
        extension.delete()

        if not holding_model.objects.filter(asset=asset).exists():
            asset.delete()

    @classmethod
    def _find_active_replacement_asset(cls, *, extension, active_snapshot_id):
        name = getattr(extension, cls.name_attr, None)
        if not name:
            return None

        replacement = (
            cls.extension_model.objects.filter(
                **{
                    f"{cls.name_attr}__iexact": name,
                    "snapshot_id": active_snapshot_id,
                }
            )
            .exclude(pk=extension.pk)
            .select_related("asset")
            .first()
        )
        if not replacement:
            return None
        return replacement.asset

    @classmethod
    def _relink_holdings_to_market_asset(cls, *, holdings_qs, target_asset, holding_model):
        touched_holding_ids = set()

        for holding in holdings_qs.select_related("account").order_by("id"):
            existing_target_holding = (
                holding_model.objects.select_for_update()
                .filter(account=holding.account, asset=target_asset)
                .exclude(pk=holding.pk)
                .first()
            )

            if not existing_target_holding:
                holding.asset = target_asset
                holding.save(update_fields=["asset", "updated_at"])
                touched_holding_ids.add(holding.id)
                continue

            cls._merge_holdings(existing_target_holding, holding)
            touched_holding_ids.add(existing_target_holding.id)

        if touched_holding_ids:
            changed_holdings = list(
                holding_model.objects.filter(id__in=touched_holding_ids).select_related("account")
            )
            cls._notify_holdings_changed(changed_holdings)

    @staticmethod
    def _merge_holdings(target, source):
        target_qty = target.quantity or Decimal("0")
        source_qty = source.quantity or Decimal("0")
        merged_qty = target_qty + source_qty

        target_avg = target.average_purchase_price
        source_avg = source.average_purchase_price

        merged_avg = None
        if merged_qty > 0 and (target_avg is not None or source_avg is not None):
            target_cost = (target_avg or Decimal("0")) * target_qty
            source_cost = (source_avg or Decimal("0")) * source_qty
            merged_avg = (target_cost + source_cost) / merged_qty

        target.quantity = merged_qty
        target.average_purchase_price = merged_avg
        if not target.original_ticker and source.original_ticker:
            target.original_ticker = source.original_ticker
            target.save(
                update_fields=[
                    "quantity",
                    "average_purchase_price",
                    "original_ticker",
                    "updated_at",
                ]
            )
        else:
            target.save(update_fields=["quantity", "average_purchase_price", "updated_at"])

        source.delete()

    @classmethod
    def _relink_market_custom_assets(cls, *, holding_model, active_snapshot_id):
        custom_assets = (
            CustomAsset.objects.filter(reason=CustomAsset.Reason.MARKET)
            .select_related("asset")
            .order_by("asset_id")
        )

        for custom_asset in custom_assets:
            if not custom_asset.asset_id:
                continue

            replacement_asset = cls._find_active_replacement_asset_for_name(
                name=custom_asset.name,
                active_snapshot_id=active_snapshot_id,
            )
            if not replacement_asset:
                continue

            holdings = holding_model.objects.select_for_update().filter(asset=custom_asset.asset)
            if not holdings.exists():
                custom_asset.asset.delete()
                continue

            cls._relink_holdings_to_market_asset(
                holdings_qs=holdings,
                target_asset=replacement_asset,
                holding_model=holding_model,
            )

            if not holding_model.objects.filter(asset=custom_asset.asset).exists():
                custom_asset.asset.delete()

    @classmethod
    def _find_active_replacement_asset_for_name(cls, *, name, active_snapshot_id):
        if not name:
            return None

        lookup = {
            f"{cls.name_attr}__iexact": name,
            "snapshot_id": active_snapshot_id,
        }
        replacement = (
            cls.extension_model.objects.filter(**lookup)
            .select_related("asset")
            .first()
        )
        if not replacement:
            return None
        return replacement.asset

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
