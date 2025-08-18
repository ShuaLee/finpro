from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from schemas.models import SchemaColumn


class SchemaColumnVisibility(models.Model):
    column = models.ForeignKey(
        SchemaColumn,
        on_delete=models.CASCADE,
        related_name="visibility_settings"
    )

    # Generic relation to any account model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    account = GenericForeignKey()

    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ("column", "content_type", "object_id")

    def __str__(self):
        return f"{self.account} | {self.column.title}: {'Visible' if self.is_visible else 'Hidden'}"
