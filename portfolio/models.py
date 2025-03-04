from django.db import models
from django.conf import settings
from core.models import Profile
# Create your models here.


class Portfolio(models.Model):
    individual_profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, null=True, blank=True
    )

    asset_manager_profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True,
        related_name='multiple_portfolios'
    )

    name = models.CharField(max_length=255, default="Portfolio")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.created_at}"

    def save(self, *args, **kwargs):
        # Ensure only the appropriate profile type gets assigned
        if self.individual_profile and self.asset_manager_profile:
            raise ValueError(
                "A portfolio cannot have both individual and asset manager profiles.")
        super().save(*args, **kwargs)
