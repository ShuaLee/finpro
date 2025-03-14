from django.db import models
from core.models import Profile
# Create your models here.


class Portfolio(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='portfolio'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile} - {self.created_at}"
