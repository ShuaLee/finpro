from django.core.exceptions import ValidationError
from django.db import models
from portfolios.models.subportfolio import SubPortfolio
from accounts.models.base import BaseAccount

# portfolio -> level0 -> level1 -> level2 (holdings can be at any level, but recommend leaves)
MAX_ACCOUNT_DEPTH = 3


class CustomAccount(BaseAccount):
    """
    Hierarchical account/folder under a Custom SubPortfolio.
    Rule: an account EITHER has children OR holdings, never both.
    """

    subportfolio = models.ForeignKey(
        SubPortfolio,
        on_delete=models.CASCADE,
        related_name="custom_accounts"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
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
                fields=["subportfolio", "parent", "name"],
                name="uniq_custom_account_name_within_parent"
            )
        ]

    def is_leaf(self) -> bool:
        return not self.children.exists()

    def has_holdings(self) -> bool:
        # Related name from CustomHolding.account
        return hasattr(self, "holdings") and self.holdings.exists()

    def clean(self):
        # Ensure parent belongs to same subportfolio
        if self.parent and self.parent.subportfolio_id != self.subportfolio_id:
            raise ValidationError(
                "Parent must belong to the same SubPortfolio.")

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
    def active_schema(self):
        """
        Return the Schema object for this subportfolio + account model
        """
        return self.subportfolio.get_schema_for_account_model("custom_account")
