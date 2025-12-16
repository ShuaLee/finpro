from django.db import models


class AccountType(models.Model):
    """
    Defines system or user-defined account categories.
    Controls:
      - How accounts behave
      - What assets they can hold (M2M to AssetType)
      - Whether multiple accounts of this type are allowed
    """

    slug = models.SlugField(unique=True, max_length=50)
    name = models.CharField(max_length=100)

    # Which asset types this account can hold
    allowed_asset_types = models.ManyToManyField(
        "assets.AssetType",
        related_name="account_types",
        blank=True,
        help_text="What asset types can be held in accounts of this type."
    )

    allows_multiple = models.BooleanField(default=True)

    is_system = models.BooleanField(default=True)

    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.name
