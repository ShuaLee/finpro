from django.db import models


class AccountType(models.Model):
    """
    Represents a user's account type (e.g., Individual Investor, Manager).
    Keeps it flexible for future expansion.
    """

    name = models.CharField(max_length=50, unique=True)  # Display name
    slug = models.SlugField(unique=True)  # For API/internal references
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"

    def __str__(self):
        return self.name