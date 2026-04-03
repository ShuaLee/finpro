from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.holdings.models import Container, Portfolio


class ContainerService:
    @staticmethod
    def create_container(
        *,
        portfolio: Portfolio,
        name: str,
        kind: str = "",
        description: str = "",
        is_tracked: bool = False,
        source: str = "",
        external_id: str = "",
        external_parent_id: str = "",
        last_synced_at=None,
    ) -> Container:
        container = Container(
            portfolio=portfolio,
            name=(name or "").strip(),
            kind=(kind or "").strip(),
            description=(description or "").strip(),
            is_tracked=is_tracked,
            source=(source or "").strip(),
            external_id=(external_id or "").strip(),
            external_parent_id=(external_parent_id or "").strip(),
            last_synced_at=last_synced_at,
        )
        container.save()
        return container

    @staticmethod
    def update_container(
        *,
        container: Container,
        profile,
        name: str | None = None,
        kind: str | None = None,
        description: str | None = None,
        is_tracked: bool | None = None,
        source: str | None = None,
        external_id: str | None = None,
        external_parent_id: str | None = None,
        last_synced_at=None,
    ) -> Container:
        if container.portfolio.profile != profile:
            raise ValidationError("You cannot edit another user's container.")

        if name is not None:
            container.name = name
        if kind is not None:
            container.kind = kind
        if description is not None:
            container.description = description
        if is_tracked is not None:
            container.is_tracked = is_tracked
        if source is not None:
            container.source = source
        if external_id is not None:
            container.external_id = external_id
        if external_parent_id is not None:
            container.external_parent_id = external_parent_id
        if last_synced_at is not None:
            container.last_synced_at = last_synced_at

        container.save()
        return container

    @staticmethod
    def mark_synced(*, container: Container) -> Container:
        container.last_synced_at = timezone.now()
        container.save(update_fields=["last_synced_at", "updated_at"])
        return container
