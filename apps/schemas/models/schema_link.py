from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class SubPortfolioSchemaLink(models.Model):
    subportfolio_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    subportfolio_id = models.PositiveIntegerField()
    subportfolio = GenericForeignKey("subportfolio_ct", "subportfolio_id")

    account_model_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="+")
    account_model = GenericForeignKey("account_model_ct", "account_model_id")
    account_model_id = models.PositiveIntegerField(null=True, blank=True)  # Always null

    schema = models.ForeignKey("Schema", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("subportfolio_ct", "subportfolio_id", "account_model_ct")