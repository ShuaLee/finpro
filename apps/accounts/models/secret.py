from django.db import models


class BrokerageSecret(models.Model):
    reference = models.CharField(max_length=255, unique=True)
    provider = models.CharField(max_length=30)
    secret_ciphertext = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

