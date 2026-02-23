from django.db import models

from profiles.models import Profile


class NavigationState(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="navigation_states",
    )
    scope = models.CharField(max_length=120)
    section_order = models.JSONField(default=list, blank=True)
    asset_item_order = models.JSONField(default=list, blank=True)
    account_item_order = models.JSONField(default=list, blank=True)
    asset_types_collapsed = models.BooleanField(default=False)
    accounts_collapsed = models.BooleanField(default=True)
    active_item_key = models.CharField(max_length=200, default="portfolio", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "scope"],
                name="uniq_navigation_state_profile_scope",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "scope"]),
        ]

    def __str__(self):
        return f"{self.profile_id}:{self.scope}"
