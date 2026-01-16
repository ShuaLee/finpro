from django.db import models

from assets.models.core import Asset
from fx.models.fx import FXCurrency
from users.models import Profile


class CustomAsset(models.Model):
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="custom",
    )

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)

    currency = models.ForeignKey(FXCurrency, on_delete=models.PROTECT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
