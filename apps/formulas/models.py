from django.db import models
from django.conf import settings
from django.utils.text import slugify



class Formula(models.Model):
    key = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Stable identifier for this formula, e.g. 'pe_ratio', 'unrealized_gain'"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Expression in terms of other source_fields
    expression = models.TextField(
        help_text="Expression using other column source_fields, e.g. '(price - purchase_price) * quantity'"
    )

    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of source_fields this formula depends on"
    )

    decimal_places = models.PositiveSmallIntegerField(
        choices=[
            (0, "0 (whole numbers)"),
            (2, "2 (cents)"),
            (4, "4 (fx/crypto standard)"),
            (8, "8 (crypto max precision)")
        ],
        null=True,
        blank=True,
        help_text="Explicit precision for calculated results"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if not self.key:
            raise ValueError("Formula must have a stable key.")
        if not self.expression:
            raise ValueError("Formula must define an expression.")
        if not isinstance(self.dependencies, list):
            raise ValueError("Formula dependencies must be a list.")
        for dep in self.dependencies:
            if not isinstance(dep, str):
                raise ValueError(f"Invalid dependency '{dep}', must be a string.")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.key})"