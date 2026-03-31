from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    language = models.CharField(max_length=16, default="en")
    timezone = models.CharField(max_length=64, default="UTC")
    currency = models.CharField(max_length=10, default="USD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name or self.user.email

    def clean(self):
        super().clean()
        if not self.pk:
            return
        original = Profile.objects.select_related(
            "user").filter(pk=self.pk).first()
        if original and original.user.pk != self.user.pk:
            raise ValidationError("Profile owner cannot be changed.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
