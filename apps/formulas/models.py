from django.db import models
from django.conf import settings
from django.utils.text import slugify

# Create your models here.
class Formula(models.Model):
    key = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Stable identifier, e.g. 'pe_ratio', 'unrealized_gain'"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Expression in terms of other formula keys
    expression = models.TextField(
        help_text="Expression in terms of other formula keys, e.g. 'price / earnings'"
    )

    dependencies = models.JSONField(default=list, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.key})"