from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from accounts.models.account import AccountType


class SubPortfolioSchemaLink(models.Model):
    subportfolio_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    subportfolio_id = models.PositiveIntegerField()
    subportfolio = GenericForeignKey("subportfolio_ct", "subportfolio_id")

    account_type = models.CharField(
        max_length=30,
        choices=AccountType.choices,
        help_text="The account type this schema is linked to.",
    )

    schema = models.ForeignKey("Schema", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("subportfolio_ct", "subportfolio_id", "account_type")
