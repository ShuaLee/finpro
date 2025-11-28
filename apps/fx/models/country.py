from django.db import models


class Country(models.Model):
    """
    ISO-3166 Alpha-2 country record.
    Populated by syncing FMP available-countries with pycountry for names.
    """
    code = models.CharField(
        max_length=2,
        primary_key=True,
        help_text="ISO-3166 alpha-2 country code (e.g., US, JP, DE)."
    )

    name = models.CharField(
        max_length=100,
        help_text="Full English name (from pycountry, or fallback to code)."
    )

    region = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Optional region grouping (e.g., Europe, APAC).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"
