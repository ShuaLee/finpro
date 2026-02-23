from django.db import models

from profiles.models import Profile


class DashboardLayoutState(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="dashboard_layout_states",
    )
    scope = models.CharField(max_length=120)
    active_layout_id = models.CharField(max_length=100, default="default")
    layouts = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "scope"],
                name="uniq_dashboard_layout_state_profile_scope",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "scope"]),
        ]

    def __str__(self):
        return f"{self.profile_id}:{self.scope}"
