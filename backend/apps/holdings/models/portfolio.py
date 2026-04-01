from django.core.exceptions import ValidationError
from django.db import models


class Portfolio(models.Model):
    class Kind(models.TextChoices):
        PERSONAL = "personal", "Personal"
        SPOUSE = "spouse", "Spouse"
        FAMILY = "family", "Family"
        OTHER = "other", "Other"

    profile = models.ForeignKey(
        "users.Profile",
        on_delete=models.CASCADE,
        related_name="portfolios",
    )

    name = models.CharField(max_length=100, default="Main Portfolio")
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.PERSONAL,
    )
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "name"],
                name="uniq_portfolio_name_per_profile",
            ),
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(is_default=True),
                name="uniq_default_portfolio_per_profile",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "is_default"]),
            models.Index(fields=["profile", "kind"]),
        ]

    def __str__(self):
        return f"{self.profile.user.email} - {self.name}"

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError("Portfolio name is required.")

        if self.pk:
            original = Portfolio.objects.only(
                "profile_id").filter(pk=self.pk).first()
            if original and original.profile.pk != self.profile.pk:
                raise ValidationError("Portfolio owner cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
