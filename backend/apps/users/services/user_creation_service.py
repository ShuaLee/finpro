from typing import cast

from django.db import transaction

from apps.users.models import User
from apps.users.models.user import UserManager
from apps.users.services.profile_creation_service import ProfileCreationService


class UserCreationService:
    @staticmethod
    @transaction.atomic
    def create_user(
        *,
        email: str,
        password: str,
        full_name: str = "",
        language: str = "en",
        timezone: str = "UTC",
        country: str = "",
        currency: str = "USD",
        is_active: bool = True,
    ) -> User:
        user_manager = cast(UserManager, User.objects)

        user = user_manager.create_user(
            email=email,
            password=password,
            is_active=is_active,
        )

        ProfileCreationService.update_profile(
            user=user,
            full_name=full_name,
            language=language,
            timezone=timezone,
            country=country,
            currency=currency,
        )

        user.refresh_from_db()
        return user
