from django.db import models
from core.models import Profile
# Create your models here.


class IndividualPortfolio(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='individual_portfolio'
    )
    name = models.CharField(max_length=255, default="Individual Portfolio")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.created_at}"
