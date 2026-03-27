import logging

from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.models import Account, AccountType
from accounts.exceptions import AccountInitializationError
from assets.models.core import AssetType
from portfolios.models import Portfolio

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    def _default_portfolio_for_profile(*, profile):
        portfolio = (
            profile.portfolios.filter(kind=Portfolio.Kind.PERSONAL)
            .order_by("id")
            .first()
        )
        if portfolio:
            return portfolio
        return profile.portfolios.order_by("id").first()

    @staticmethod
    def _generate_account_name(*, portfolio, account_type, requested_name: str | None):
        base_name = (requested_name or "").strip() or account_type.name
        candidate = base_name
        suffix = 2
        while Account.objects.filter(
            portfolio=portfolio,
            account_type=account_type,
            name__iexact=candidate,
        ).exists():
            candidate = f"{base_name} {suffix}"
            suffix += 1
        return candidate

    @staticmethod
    @transaction.atomic
    def initialize_account(*, account, definition=None, profile=None):
        """
        Initialize account foundations.

        Best-effort (if schemas app is enabled):
        - ensure the default schema for this account's resolved asset context
        - initialize column visibility for account
        """
        logger.info(
            "Initializing account %s (%s)",
            account.id,
            account.name,
        )

        try:
            profile = profile or account.portfolio.profile

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
                    metadata={},
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
        portfolio_id: int | None = None,
        name: str | None = None,
        account_type_id: int,
        position_mode: str | None = None,
        allow_manual_overrides: bool | None = None,
        enforce_restrictions: bool | None = None,
        allowed_asset_type_slugs: list[str] | None = None,
    ):
        portfolio = None
        if portfolio_id is not None:
            portfolio = Portfolio.objects.filter(id=portfolio_id, profile=profile).first()
        else:
            portfolio = AccountService._default_portfolio_for_profile(profile=profile)
        if not portfolio:
            raise ValidationError("Portfolio not found.")

        account_type = AccountType.objects.filter(id=account_type_id).first()
        if not account_type:
            raise ValidationError("Account type not found.")

        if not account_type.is_system and account_type.owner_id != profile.id:
            raise ValidationError("You cannot use another user's custom account type.")

        selected_asset_types = None
        if allowed_asset_type_slugs is not None:
            selected_asset_types = list(AssetType.objects.filter(slug__in=allowed_asset_type_slugs))
            if len(selected_asset_types) != len(set(allowed_asset_type_slugs)):
                raise ValidationError("One or more allowed asset types are invalid.")

        account = Account.objects.create(
            portfolio=portfolio,
            name=AccountService._generate_account_name(
                portfolio=portfolio,
                account_type=account_type,
                requested_name=name,
            ),
            account_type=account_type,
            position_mode=position_mode or Account.PositionMode.MANUAL,
            allow_manual_overrides=True if allow_manual_overrides is None else allow_manual_overrides,
            enforce_restrictions=False if enforce_restrictions is None else enforce_restrictions,
        )

        if selected_asset_types is not None:
            account.allowed_asset_types.set(selected_asset_types)
            if enforce_restrictions is None:
                account.enforce_restrictions = False
                account.save(update_fields=["enforce_restrictions"])

        return AccountService.initialize_account(
            account=account,
            profile=profile,
        )
