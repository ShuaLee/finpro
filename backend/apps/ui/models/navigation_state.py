from django.db import models


class NavigationState(models.Model):
    profile = models.ForeignKey(
        "users.Profile",
        on_delete=models.CASCADE,
        related_name="ui_navigation_states",
    )
    scope = models.CharField(max_length=80)
    section_order = models.JSONField(default=list, blank=True)
    asset_item_order = models.JSONField(default=list, blank=True)
    account_item_order = models.JSONField(default=list, blank=True)
    asset_types_collapsed = models.BooleanField(default=False)
    accounts_collapsed = models.BooleanField(default=False)
    active_item_key = models.CharField(max_length=160, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scope"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "scope"],
                name="uniq_ui_navigation_state_per_profile_scope",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "scope"]),
        ]

    def __str__(self):
        return f"{self.profile.user.email} - {self.scope}"
