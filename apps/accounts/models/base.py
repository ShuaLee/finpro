from django.contrib.contenttypes.models import ContentType
from django.db import models
from schemas.models import SchemaColumnVisibility


class BaseAccount(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
    
    def initialize_visibility_settings(self, schema):
        """
        Sets up SchemaColumnVisibility rows for this account based on the given schema.
        Should be called once, right after account creation.
        """
        ct = ContentType.objects.get_for_model(self.__class__)
        for column in schema.columns.all():
            SchemaColumnVisibility.objects.get_or_create(
                content_type=ct,
                object_id=self.id,
                column=column,
                defaults={'is_visible': True}
            )
    
    def get_visible_columns(self):
        """
        Returns visible SchemaColumns for this account.
        """
        ct = ContentType.objects.get_for_model(self.__class__)
        return SchemaColumnVisibility.objects.filter(
            content_type=ct,
            object_id=self.id,
            is_visible=True
        ).select_related("column")