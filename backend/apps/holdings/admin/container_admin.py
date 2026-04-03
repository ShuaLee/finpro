from django.contrib import admin

from apps.holdings.models import Container


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "portfolio",
        "kind",
        "is_tracked",
        "source",
        "last_synced_at",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "is_tracked",
        "source",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "name",
        "description",
        "kind",
        "portfolio__name",
        "portfolio__profile__user__email",
        "external_id",
        "external_parent_id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("portfolio", "name")

