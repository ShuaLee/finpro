from django.core.exceptions import ValidationError
from django.db import models


class Container(models.Model):
    portfolio = models.ForeignKey(
        "holdings.Portfolio",
        on_delete=models.CASCADE,
        related_name="containers",
    )
    name = models.CharField(max_length=100)
    kind = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional user-defined category, such as Brokerage, Private Equity, Funds, Wallet, Garage, or Vault.",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional short explanation for what this container represents.",
    )
    is_tracked = models.BooleanField(default=False)
    source = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional external source for this container, such as Plaid.",
    )
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional external account identifier for tracked containers.",
    )
    external_parent_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional external connection identifier for tracked containers.",
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "name"],
                name="uniq_container_name_per_portfolio",
            ),
        ]
        indexes = [
            models.Index(fields=["portfolio", "kind"]),
        ]

    def __str__(self):
        return f"{self.portfolio.name} - {self.name}"

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.kind = (self.kind or "").strip()
        self.description = (self.description or "").strip()
        self.source = (self.source or "").strip()
        self.external_id = (self.external_id or "").strip()
        self.external_parent_id = (self.external_parent_id or "").strip()

        if not self.name:
            raise ValidationError("Container name is required.")

        if self.pk:
            original = (
                Container.objects
                .select_related("portfolio")
                .only("portfolio")
                .filter(pk=self.pk)
                .first()
            )
            if original and original.portfolio.pk != self.portfolio.pk:
                raise ValidationError("Container portfolio cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
