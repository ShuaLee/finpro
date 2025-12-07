from django.db import models


class DataType(models.Model):
    """
    Defines a fundamental data shape, such as:
    - decimal
    - string
    - date
    - url
    """

    # e.g., "decimal", "string"
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(
        max_length=100, unique=True)              # Human name
    description = models.TextField(blank=True, null=True)

    # Capability flags to determine which constraint types apply
    supports_length = models.BooleanField(
        default=False)            # string, url
    supports_decimals = models.BooleanField(default=False)          # decimal
    supports_numeric_limits = models.BooleanField(default=False)    # decimal
    supports_regex = models.BooleanField(
        default=False)             # string, url

    is_system = models.BooleanField(default=True)  # protects from deletion

    class Meta:
        ordering = ["slug"]

    def __str__(self):
        return self.name
