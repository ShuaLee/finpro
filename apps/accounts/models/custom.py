from django.core.exceptions import ValidationError
from django.db import models
from portfolios.models.custom import CustomPortfolio
from accounts.models.base import BaseAccount

# portfolio -> level0 -> level1 -> level2 (holdings can be at any level, but recommend leaves)
MAX_ACCOUNT_DEPTH = 3


class CustomAccount(BaseAccount):
    """
    Hierarchical account/folder under a CustomPortfolio.
    Rule: an account EITHER has children OR holdings, never both.
    """
    custom_portfolio = models.ForeignKey(
        CustomPortfolio,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )

    # Cached depth for validation/queries (0 for root)
    depth = models.PositiveSmallIntegerField(default=0, editable=False)

    asset_type = "custom"
    account_variant = "custom_account"

    class Meta:
        verbose_name = "Custom Account"
        constraints = [
            # ✅ Unique name among siblings (including top level where parent is NULL)
            models.UniqueConstraint(
                fields=['custom_portfolio', 'parent', 'name'],
                name='uniq_custom_account_name_within_parent'
            )
        ]

    def is_leaf(self) -> bool:
        return not self.children.exist()

    def has_holdings(self) -> bool:
        # Related name from CustomHolding.account
        return hasattr(self, "holdings") and self.holdings.exists()

    def clean(self):
        # Ensure parent belongs to same portfolio
        if self.parent and self.parent.custom_portfolio_id != self.custom_portfolio_id:
            raise ValidationError(
                "Parent must belong to the same CustomPortfolio.")

        # Compute depth & enforce max depth
        d = 0
        cur = self.parent
        while cur:
            d += 1
            if d >= MAX_ACCOUNT_DEPTH:
                raise ValidationError(
                    f"Maximum account depth is {MAX_ACCOUNT_DEPTH}")
            cur = cur.parent
        self.depth = d

        # exclusivity rule (container vs leaf):
        # If this account has holdings, it cannot have children
        # (We can't query self.children on unsaved brand-new instance with pending changes,
        #  so we validate the *parent* when adding a child; see below.)
        # Note: here we only enforce the case "has children -> no holdings" on the *parent*.
        if self.parent:
            # You are creating/moving this account under `parent` -> parent must not have holdings
            if getattr(self.parent, "holdings", None) and self.parent.holdings.exists():
                raise ValidationError(
                    "Cannot add a child to an account that already has holdings.")

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def sub_portfolio(self):
        return self.custom_portfolio

    @property
    def active_schema(self):
        # Return the Schema object for this portfolio + account model
        return self.custom_portfolio.get_schema_for_account_model(type(self))
