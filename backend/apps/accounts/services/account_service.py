import logging

from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.models import Account, AccountType
from accounts.exceptions import AccountInitializationError
from accounts.models.account_classification import AccountClassification
from accounts.models.account_classification import ClassificationDefinition
from assets.models.core import AssetType
from portfolios.models import Portfolio

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition, profile=None):
        """
        Initialize account foundations.

        Always:
        - attach/create AccountClassification

        Best-effort (if schemas app is enabled):
        - ensure schema for (portfolio, account_type)
        - initialize column visibility for account
        """
        logger.info(
            "Initializing account %s (%s) with classification %s",
            account.id,
            account.name,
            definition.name,
        )

        try:
            profile = profile or account.portfolio.profile

            classification, _ = AccountClassification.objects.get_or_create(
                profile=profile,
                definition=definition,
            )

            if account.classification_id != classification.id:
                account.classification = classification
                account.save(update_fields=["classification"])

            # Optional schema integration.
            try:
                from schemas.services.bootstrap import SchemaBootstrapService
                from schemas.services.mutations import SchemaMutationService
            except Exception:
                logger.info(
                    "Schemas app unavailable; skipping schema initialization for account %s",
                    account.id,
                )
                return account

            schema = SchemaBootstrapService.ensure_for_account(account)
            SchemaMutationService.initialize_visibility_for_account(account=account)
            logger.info(
                "Schema %s ensured for account %s",
                getattr(schema, "id", None),
                account.id,
            )
            try:
                from accounts.services.audit_service import AccountAuditService
                AccountAuditService.log(
                    account=account,
                    action="account.initialized",
                    metadata={"classification_id": classification.id},
                )
            except Exception:
                pass
            return account
        except Exception as exc:
            logger.error(
                "Failed to initialize account %s: %s",
                account.id,
                exc,
                exc_info=True,
            )
            raise AccountInitializationError(
                f"Failed to initialize account {account.id}: {exc}"
            ) from exc

    @staticmethod
    @transaction.atomic
    def create_custom_account_type(*, profile, name: str, description: str | None, allowed_asset_type_slugs: list[str]):
        asset_types = list(AssetType.objects.filter(slug__in=allowed_asset_type_slugs))
        if len(asset_types) != len(set(allowed_asset_type_slugs)):
            raise ValidationError("One or more allowed asset types are invalid.")

        account_type = AccountType.objects.create(
            name=name,
            is_system=False,
            owner=profile,
            description=description or "",
        )
        account_type.allowed_asset_types.set(asset_types)
        return account_type

    @staticmethod
    @transaction.atomic
    def create_account(
        *,
        profile,
        portfolio_id: int,
        name: str,
        account_type_id: int,
        broker: str | None,
        classification_definition_id: int,
        position_mode: str | None = None,
        allow_manual_overrides: bool | None = None,
    ):
        portfolio = Portfolio.objects.filter(id=portfolio_id, profile=profile).first()
        if not portfolio:
            raise ValidationError("Portfolio not found.")

        account_type = AccountType.objects.filter(id=account_type_id).first()
        if not account_type:
            raise ValidationError("Account type not found.")

        if not account_type.is_system and account_type.owner_id != profile.id:
            raise ValidationError("You cannot use another user's custom account type.")

        definition = ClassificationDefinition.objects.filter(id=classification_definition_id).first()
        if not definition:
            raise ValidationError("Classification definition not found.")

        account = Account.objects.create(
            portfolio=portfolio,
            name=name,
            account_type=account_type,
            broker=(broker or "").strip() or None,
            position_mode=position_mode or Account.PositionMode.MANUAL,
            allow_manual_overrides=True if allow_manual_overrides is None else allow_manual_overrides,
        )

        return AccountService.initialize_account(
            account=account,
            definition=definition,
            profile=profile,
        )
