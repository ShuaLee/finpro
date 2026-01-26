from django.db import models


class SchemaTemplate(models.Model):
    """
    Blueprint for generating schemas.
    """

    name = models.CharField(max_length=255)

    account_type = models.ForeignKey(
        "accounts.AccountType",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="NULL = base template for custom account types",
    )

    is_base = models.BooleanField(
        default=False,
        help_text="True for the fallback template",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account_type"],
                condition=models.Q(is_base=False),
                name="one_active_template_per_account_type",
            ),
            models.UniqueConstraint(
                fields=["is_base"],
                condition=models.Q(is_base=True),
                name="only_one_base_template",
            ),
        ]

    def __str__(self):
        return self.name
